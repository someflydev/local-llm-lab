from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from lab.model_registry import recommend
from lab.ollama_client import OllamaClient
from lab.rag import answer_question


APP_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_ROOT / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app = FastAPI(title="Local LLM Lab")


def _latest_run_summaries(limit: int = 20) -> list[dict[str, Any]]:
    runs_root = Path("runs")
    if not runs_root.exists():
        return []

    summaries: list[dict[str, Any]] = []
    for run_dir in sorted([p for p in runs_root.iterdir() if p.is_dir()], reverse=True):
        summary_path = run_dir / "summary.json"
        if not summary_path.exists():
            continue
        try:
            data = orjson.loads(summary_path.read_bytes())
            data["run_dir"] = str(run_dir)
            summaries.append(data)
        except Exception:
            continue
        if len(summaries) >= limit:
            break
    return summaries


def _load_run_detail(run_id: str) -> dict[str, Any] | None:
    run_dir = Path("runs") / run_id
    summary_path = run_dir / "summary.json"
    results_path = run_dir / "results.jsonl"
    if not summary_path.exists():
        return None

    summary = orjson.loads(summary_path.read_bytes())
    rows: list[dict[str, Any]] = []
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines()[:100]:
            if line.strip():
                rows.append(orjson.loads(line))
    return {"summary": summary, "results": rows}


def _recommended_model(task: str) -> str | None:
    try:
        return recommend(task).get("chosen_model")
    except Exception:
        return None


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.api_route("/chat", methods=["GET", "POST"], response_class=HTMLResponse)
def chat_page(
    request: Request,
    prompt: str = Form(default=""),
    model: str = Form(default=""),
    temperature: float = Form(default=0.2),
    num_ctx: int = Form(default=4096),
) -> HTMLResponse:
    result: dict[str, Any] | None = None
    error: str | None = None
    if request.method == "POST":
        chosen_model = model or _recommended_model("chat")
        if not chosen_model:
            error = "No chat model is installed. Try `ollama pull llama3`."
        else:
            try:
                result = OllamaClient().chat_generate(
                    model=chosen_model,
                    prompt=prompt,
                    temperature=temperature,
                    num_ctx=num_ctx,
                )
                result["model"] = chosen_model
            except Exception as exc:
                error = str(exc)

    context = {
        "request": request,
        "prompt": prompt,
        "model": model or (_recommended_model("chat") or ""),
        "temperature": temperature,
        "num_ctx": num_ctx,
        "result": result,
        "error": error,
    }
    return templates.TemplateResponse("chat.html", context)


@app.api_route("/rag", methods=["GET", "POST"], response_class=HTMLResponse)
def rag_page(
    request: Request,
    question: str = Form(default=""),
    index_dir: str = Form(default="runs/index"),
    model: str = Form(default=""),
    embed_model: str = Form(default=""),
    k: int = Form(default=5),
    temperature: float = Form(default=0.2),
    num_ctx: int = Form(default=4096),
) -> HTMLResponse:
    result: dict[str, Any] | None = None
    error: str | None = None
    if request.method == "POST":
        chosen_model = model or _recommended_model("rag_qa")
        chosen_embed = embed_model or _recommended_model("embeddings")
        if not chosen_model:
            error = "No RAG chat model installed. Try `ollama pull llama3`."
        elif not chosen_embed:
            error = "No embeddings model installed. Try `ollama pull nomic-embed-text`."
        else:
            try:
                result = answer_question(
                    question=question,
                    index_dir=index_dir,
                    chat_model_name=chosen_model,
                    embed_model_name=chosen_embed,
                    k=k,
                    temperature=temperature,
                    num_ctx=num_ctx,
                )
                result["model"] = chosen_model
                result["embed_model"] = chosen_embed
            except Exception as exc:
                error = str(exc)

    context = {
        "request": request,
        "question": question,
        "index_dir": index_dir,
        "model": model or (_recommended_model("rag_qa") or ""),
        "embed_model": embed_model or (_recommended_model("embeddings") or ""),
        "k": k,
        "temperature": temperature,
        "num_ctx": num_ctx,
        "result": result,
        "error": error,
    }
    return templates.TemplateResponse("rag.html", context)


@app.get("/runs", response_class=HTMLResponse)
def runs_page(request: Request) -> HTMLResponse:
    summaries = _latest_run_summaries()
    return templates.TemplateResponse("runs.html", {"request": request, "summaries": summaries})


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail_page(request: Request, run_id: str) -> HTMLResponse:
    detail = _load_run_detail(run_id)
    if detail is None:
        return templates.TemplateResponse(
            "run_detail.html",
            {"request": request, "run_id": run_id, "error": "Run not found", "summary": None, "results": []},
            status_code=404,
        )
    return templates.TemplateResponse(
        "run_detail.html",
        {
            "request": request,
            "run_id": run_id,
            "summary": detail["summary"],
            "results": detail["results"],
            "error": None,
        },
    )

