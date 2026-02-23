from __future__ import annotations

import asyncio
import logging
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
logger = logging.getLogger(__name__)


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


def _read_jsonl_preview(path: Path, limit: int = 100) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    truncated = False
    with path.open("rb") as fh:
        for line_num, raw_line in enumerate(fh, start=1):
            if line_num > limit:
                truncated = True
                break
            line = raw_line.strip()
            if not line:
                continue
            rows.append(orjson.loads(line))
    return rows, truncated


def _load_run_detail(run_id: str, preview_limit: int = 100) -> dict[str, Any] | None:
    run_dir = Path("runs") / run_id
    summary_path = run_dir / "summary.json"
    results_path = run_dir / "results.jsonl"
    if not summary_path.exists():
        return None

    summary = orjson.loads(summary_path.read_bytes())
    rows: list[dict[str, Any]] = []
    truncated = False
    if results_path.exists():
        rows, truncated = _read_jsonl_preview(results_path, limit=preview_limit)
    return {"summary": summary, "results": rows, "results_truncated": truncated, "preview_limit": preview_limit}


def _recommended_model(task: str) -> str | None:
    try:
        return recommend(task).get("chosen_model")
    except Exception:
        logger.exception("Failed to compute recommended model for task=%s", task)
        return None


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.api_route("/chat", methods=["GET", "POST"], response_class=HTMLResponse)
async def chat_page(
    request: Request,
    prompt: str = Form(default=""),
    model: str = Form(default=""),
    temperature: float = Form(default=0.2),
    num_ctx: int = Form(default=4096),
) -> HTMLResponse:
    result: dict[str, Any] | None = None
    error: str | None = None
    warnings: list[str] = []
    default_chat_model = await asyncio.to_thread(_recommended_model, "chat")
    if not default_chat_model:
        warnings.append("Could not compute a recommended chat model. Check logs and local model policy.")
    if request.method == "POST":
        chosen_model = model or default_chat_model
        if not chosen_model:
            error = "No chat model is installed. Try `ollama pull llama3`."
        else:
            try:
                result = await asyncio.to_thread(
                    OllamaClient().chat_generate,
                    model=chosen_model,
                    prompt=prompt,
                    temperature=temperature,
                    num_ctx=num_ctx,
                )
                result["model"] = chosen_model
            except Exception as exc:
                logger.exception("Chat UI request failed")
                error = str(exc)

    context = {
        "request": request,
        "prompt": prompt,
        "model": model or (default_chat_model or ""),
        "temperature": temperature,
        "num_ctx": num_ctx,
        "result": result,
        "error": error,
        "warnings": warnings,
    }
    return templates.TemplateResponse("chat.html", context)


@app.api_route("/rag", methods=["GET", "POST"], response_class=HTMLResponse)
async def rag_page(
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
    warnings: list[str] = []
    default_chat_model = await asyncio.to_thread(_recommended_model, "rag_qa")
    default_embed_model = await asyncio.to_thread(_recommended_model, "embeddings")
    if not default_chat_model:
        warnings.append("Could not compute a recommended RAG chat model. Check logs and local model policy.")
    if not default_embed_model:
        warnings.append("Could not compute a recommended embeddings model. Check logs and local model policy.")
    if request.method == "POST":
        chosen_model = model or default_chat_model
        chosen_embed = embed_model or default_embed_model
        if not chosen_model:
            error = "No RAG chat model installed. Try `ollama pull llama3`."
        elif not chosen_embed:
            error = "No embeddings model installed. Try `ollama pull nomic-embed-text`."
        else:
            try:
                result = await asyncio.to_thread(
                    answer_question,
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
                logger.exception("RAG UI request failed")
                error = str(exc)

    context = {
        "request": request,
        "question": question,
        "index_dir": index_dir,
        "model": model or (default_chat_model or ""),
        "embed_model": embed_model or (default_embed_model or ""),
        "k": k,
        "temperature": temperature,
        "num_ctx": num_ctx,
        "result": result,
        "error": error,
        "warnings": warnings,
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
            "results_truncated": detail["results_truncated"],
            "preview_limit": detail["preview_limit"],
            "error": None,
        },
    )
