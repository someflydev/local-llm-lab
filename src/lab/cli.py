from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.table import Table

from lab.doctor import run_doctor
from lab.ingest import ingest_corpus
from lab.model_registry import match_installed_to_policy, recommend
from lab.ollama_client import OllamaClient
from lab.rag import answer_question
from lab.reporting import compare_runs, print_run_summary
from lab.retrieval import retrieve
from lab.runner import run_config


console = Console()


def _cmd_doctor(args: argparse.Namespace) -> int:
    return run_doctor(base_url=args.base_url)


def _cmd_models_list(_: argparse.Namespace) -> int:
    client = OllamaClient()
    try:
        models = client.list_models()
    except Exception as exc:
        console.print(f"[red]Failed to list models:[/red] {exc}")
        return 1

    if not models:
        console.print("[yellow]No models installed.[/yellow]")
        console.print("Recommended: `ollama pull llama3`")
        return 0

    console.print("[bold]Installed models[/bold]")
    for name in models:
        console.print(f"- {name}")
    return 0


def _cmd_models_status(_: argparse.Namespace) -> int:
    try:
        matches = match_installed_to_policy()
    except Exception as exc:
        console.print(f"[red]Failed to evaluate model policy status:[/red] {exc}")
        return 1

    table = Table(title="Model Policy Status")
    table.add_column("Bucket", style="bold")
    table.add_column("Models")

    ordered_buckets = [
        ("available_known_good", "Available known-good"),
        ("available_preferred_variants", "Available preferred variants"),
        ("available_embeddings", "Available embeddings"),
        ("available_candidates", "Available candidates"),
        ("missing_recommended", "Missing recommended"),
    ]

    for key, label in ordered_buckets:
        entries = matches.get(key, [])
        text = ", ".join(entry.name for entry in entries) if entries else "-"
        table.add_row(label, text)

    console.print(table)
    return 0


def _cmd_models_recommend(args: argparse.Namespace) -> int:
    try:
        rec = recommend(args.task)
    except Exception as exc:
        console.print(f"[red]Failed to compute recommendation:[/red] {exc}")
        return 1

    console.print(f"[bold]Task:[/bold] {args.task}")
    console.print(f"[bold]Chosen model:[/bold] {rec['chosen_model'] or 'None'}")
    console.print(f"[bold]Reason:[/bold] {rec['reason']}")
    console.print(
        "[bold]Defaults:[/bold] "
        f"temperature={rec['defaults']['temperature']} "
        f"num_ctx={rec['defaults']['num_ctx']}"
    )
    if rec["suggested_pulls"]:
        console.print("[bold]Suggested pulls:[/bold]")
        for name in rec["suggested_pulls"]:
            console.print(f"- ollama pull {name}")
    return 0


def _pick_default_model(client: OllamaClient) -> str | None:
    models = client.list_models()
    for name in models:
        if name.startswith("llama3"):
            return name
    return models[0] if models else None


def _recommended_embeddings_model() -> tuple[str | None, list[str]]:
    rec = recommend("embeddings")
    return rec.get("chosen_model"), rec.get("suggested_pulls", [])


def _recommended_task_model(task: str) -> tuple[str | None, list[str]]:
    rec = recommend(task)  # type: ignore[arg-type]
    return rec.get("chosen_model"), rec.get("suggested_pulls", [])


def _cmd_chat(args: argparse.Namespace) -> int:
    client = OllamaClient()
    model = args.model
    try:
        if not model:
            model = _pick_default_model(client)
    except Exception as exc:
        console.print(f"[red]Failed to discover models:[/red] {exc}")
        return 1

    if not model:
        console.print("[yellow]No local models installed. Try:[/yellow] `ollama pull llama3`")
        return 1

    try:
        result = client.chat_generate(
            model=model,
            prompt=args.prompt,
            temperature=args.temperature,
            num_ctx=args.num_ctx,
        )
    except Exception as exc:
        console.print(f"[red]Chat request failed:[/red] {exc}")
        return 1

    console.print(f"[bold]Model:[/bold] {model}")
    console.print(f"[bold]Latency:[/bold] {result['latency_ms']} ms")
    console.print()
    console.print(result["text"] or "[dim](empty response)[/dim]")
    if args.show_raw:
        console.print()
        console.print("[dim]Raw response snippet:[/dim]")
        console.print(result["raw_response_snippet"])
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    embed_model = args.embed_model
    if not embed_model:
        try:
            embed_model, suggestions = _recommended_embeddings_model()
        except Exception as exc:
            console.print(f"[red]Failed to resolve embeddings model recommendation:[/red] {exc}")
            return 1
        if not embed_model:
            console.print("[red]No installed embeddings model matched the policy.[/red]")
            for name in suggestions:
                console.print(f"- ollama pull {name}")
            return 1

    try:
        metadata = ingest_corpus(
            corpus_dir=args.corpus,
            index_dir=args.index,
            embed_model_name=embed_model,
            chunk_size_chars=args.chunk_size_chars,
            overlap_chars=args.overlap_chars,
        )
    except Exception as exc:
        console.print(f"[red]Ingest failed:[/red] {exc}")
        return 1

    console.print("[bold green]Ingest complete[/bold green]")
    for key, value in metadata.items():
        console.print(f"- {key}: {value}")
    return 0


def _cmd_retrieve(args: argparse.Namespace) -> int:
    embed_model = args.embed_model
    if not embed_model:
        try:
            embed_model, suggestions = _recommended_embeddings_model()
        except Exception as exc:
            console.print(f"[red]Failed to resolve embeddings model recommendation:[/red] {exc}")
            return 1
        if not embed_model:
            console.print("[red]No installed embeddings model matched the policy.[/red]")
            for name in suggestions:
                console.print(f"- ollama pull {name}")
            return 1

    try:
        results = retrieve(
            query=args.query,
            k=args.k,
            index_dir=args.index,
            embed_model_name=embed_model,
        )
    except Exception as exc:
        console.print(f"[red]Retrieve failed:[/red] {exc}")
        return 1

    console.print(f"[bold]Top {len(results)} results[/bold] (embed model: {embed_model})")
    for item in results:
        console.print(
            f"- path={item['path']} chunk_id={item['chunk_id']} score={item['score']:.4f}\n"
            f"  snippet={item['snippet']}"
        )
    return 0


def _cmd_rag(args: argparse.Namespace) -> int:
    chat_model = args.model
    embed_model = args.embed_model

    try:
        if not chat_model:
            chat_model, chat_suggestions = _recommended_task_model("rag_qa")
        else:
            chat_suggestions = []
        if not embed_model:
            embed_model, embed_suggestions = _recommended_embeddings_model()
        else:
            embed_suggestions = []
    except Exception as exc:
        console.print(f"[red]Failed to resolve model recommendations:[/red] {exc}")
        return 1

    if not chat_model:
        console.print("[red]No installed chat/RAG model matched the policy.[/red]")
        for name in chat_suggestions:
            console.print(f"- ollama pull {name}")
        return 1
    if not embed_model:
        console.print("[red]No installed embeddings model matched the policy.[/red]")
        for name in embed_suggestions:
            console.print(f"- ollama pull {name}")
        return 1

    try:
        result = answer_question(
            question=args.question,
            index_dir=args.index,
            chat_model_name=chat_model,
            embed_model_name=embed_model,
            k=args.k,
            temperature=args.temperature,
            num_ctx=args.num_ctx,
            question_id=args.question_id,
        )
    except Exception as exc:
        console.print(f"[red]RAG failed:[/red] {exc}")
        return 1

    console.print(f"[bold]Model:[/bold] {chat_model}")
    console.print(f"[bold]Embeddings:[/bold] {embed_model}")
    console.print(f"[bold]Latency:[/bold] {result['latency_ms']} ms")
    console.print()
    console.print(result["answer_text"])
    if result["retrieved"]:
        console.print()
        console.print("[bold]Retrieved[/bold]")
        for item in result["retrieved"]:
            console.print(
                f"- path={item['path']} chunk_id={item['chunk_id']} score={item['score']:.4f}"
            )
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        run_dir = run_config(args.config)
    except Exception as exc:
        console.print(f"[red]Run failed:[/red] {exc}")
        return 1
    console.print(f"[bold green]Run complete:[/bold green] {run_dir}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    try:
        print_run_summary(args.run)
    except Exception as exc:
        console.print(f"[red]Report failed:[/red] {exc}")
        return 1
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    try:
        compare_runs(args.runs)
    except Exception as exc:
        console.print(f"[red]Compare failed:[/red] {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lab", description="Local LLM Lab CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_doctor = subparsers.add_parser("doctor", help="Check local environment and Ollama connectivity")
    p_doctor.add_argument("--base-url", default="http://127.0.0.1:11434", help="Ollama HTTP base URL")
    p_doctor.set_defaults(func=_cmd_doctor)

    p_models = subparsers.add_parser("models", help="Inspect local models")
    models_sub = p_models.add_subparsers(dest="models_command", required=True)

    p_models_list = models_sub.add_parser("list", help="List installed Ollama models")
    p_models_list.set_defaults(func=_cmd_models_list)

    p_models_status = models_sub.add_parser("status", help="Show model registry policy vs installed models")
    p_models_status.set_defaults(func=_cmd_models_status)

    p_models_recommend = models_sub.add_parser("recommend", help="Recommend a model for a task")
    p_models_recommend.add_argument("--task", required=True, choices=["chat", "rag_qa", "embeddings"])
    p_models_recommend.set_defaults(func=_cmd_models_recommend)

    p_chat = subparsers.add_parser("chat", help="Run one-shot local chat inference")
    p_chat.add_argument("--prompt", required=True, help="User prompt text")
    p_chat.add_argument("--model", default=None, help="Model name (defaults to llama3 if installed)")
    p_chat.add_argument("--temperature", type=float, default=0.2)
    p_chat.add_argument("--num-ctx", type=int, default=4096, dest="num_ctx")
    p_chat.add_argument("--show-raw", action="store_true", help="Print raw response snippet")
    p_chat.set_defaults(func=_cmd_chat)

    p_ingest = subparsers.add_parser("ingest", help="Build local embeddings index from a corpus")
    p_ingest.add_argument("--corpus", default="data/corpus", help="Corpus directory")
    p_ingest.add_argument("--index", default="runs/index", help="Index directory")
    p_ingest.add_argument("--embed-model", default=None, dest="embed_model", help="Embeddings model name")
    p_ingest.add_argument("--chunk-size-chars", type=int, default=900, dest="chunk_size_chars")
    p_ingest.add_argument("--overlap-chars", type=int, default=120, dest="overlap_chars")
    p_ingest.set_defaults(func=_cmd_ingest)

    p_retrieve = subparsers.add_parser("retrieve", help="Retrieve top-k chunks from local index")
    p_retrieve.add_argument("--index", default="runs/index", help="Index directory")
    p_retrieve.add_argument("--query", required=True, help="Query text")
    p_retrieve.add_argument("--k", type=int, default=5)
    p_retrieve.add_argument("--embed-model", default=None, dest="embed_model", help="Embeddings model name")
    p_retrieve.set_defaults(func=_cmd_retrieve)

    p_rag = subparsers.add_parser("rag", help="Answer a question using local retrieval + Ollama")
    p_rag.add_argument("--index", default="runs/index", help="Index directory")
    p_rag.add_argument("--question", required=True, help="User question")
    p_rag.add_argument("--question-id", default=None, dest="question_id", help="Optional dataset id")
    p_rag.add_argument("--model", default=None, help="Chat model name")
    p_rag.add_argument("--embed-model", default=None, dest="embed_model", help="Embeddings model name")
    p_rag.add_argument("--k", type=int, default=5)
    p_rag.add_argument("--num-ctx", type=int, default=4096, dest="num_ctx")
    p_rag.add_argument("--temperature", type=float, default=0.2)
    p_rag.set_defaults(func=_cmd_rag)

    p_run = subparsers.add_parser("run", help="Run an experiment config")
    p_run.add_argument("--config", required=True, help="Path to experiment config YAML")
    p_run.set_defaults(func=_cmd_run)

    p_report = subparsers.add_parser("report", help="Print a run summary")
    p_report.add_argument("--run", required=True, help="Run directory (e.g., runs/<run_id>)")
    p_report.set_defaults(func=_cmd_report)

    p_compare = subparsers.add_parser("compare", help="Compare two or more runs")
    p_compare.add_argument("--runs", nargs="+", required=True, help="Run directories")
    p_compare.set_defaults(func=_cmd_compare)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 2
    return int(func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
