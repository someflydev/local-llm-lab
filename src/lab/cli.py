from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.table import Table

from lab.doctor import run_doctor
from lab.model_registry import match_installed_to_policy, recommend
from lab.ollama_client import OllamaClient


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
