from __future__ import annotations

import asyncio
import logging
import uuid
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
JOB_STORE: dict[str, dict[str, Any]] = {}


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


def _read_jsonl_window(path: Path, offset: int = 0, limit: int = 100) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    has_more = False
    wanted_start = max(0, offset)
    wanted_limit = max(1, min(limit, 500))
    taken = 0
    seen = 0
    with path.open("rb") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            if seen < wanted_start:
                seen += 1
                continue
            if taken >= wanted_limit:
                has_more = True
                break
            rows.append(orjson.loads(line))
            seen += 1
            taken += 1
    return rows, has_more


def _load_run_detail(run_id: str, offset: int = 0, limit: int = 100) -> dict[str, Any] | None:
    run_dir = Path("runs") / run_id
    summary_path = run_dir / "summary.json"
    results_path = run_dir / "results.jsonl"
    if not summary_path.exists():
        return None

    summary = orjson.loads(summary_path.read_bytes())
    rows: list[dict[str, Any]] = []
    has_more = False
    offset = max(0, offset)
    limit = max(1, min(limit, 500))
    if results_path.exists():
        rows, has_more = _read_jsonl_window(results_path, offset=offset, limit=limit)
    return {
        "summary": summary,
        "results": rows,
        "results_truncated": has_more,
        "offset": offset,
        "preview_limit": limit,
        "prev_offset": max(0, offset - limit) if offset > 0 else None,
        "next_offset": (offset + limit) if has_more else None,
    }


def _recommended_model(task: str) -> str | None:
    try:
        return recommend(task).get("chosen_model")
    except Exception:
        logger.exception("Failed to compute recommended model for task=%s", task)
        return None


def _job_public(job_id: str) -> dict[str, Any]:
    raw = JOB_STORE[job_id]
    return {
        "job_id": job_id,
        "kind": raw["kind"],
        "status": raw["status"],
        "created_at": raw["created_at"],
        "started_at": raw.get("started_at"),
        "finished_at": raw.get("finished_at"),
        "error": raw.get("error"),
        "result": raw.get("result"),
    }


async def _run_job(job_id: str, kind: str, func: Any, kwargs: dict[str, Any]) -> None:
    job = JOB_STORE[job_id]
    job["status"] = "running"
    job["started_at"] = asyncio.get_running_loop().time()
    try:
        result = await asyncio.to_thread(func, **kwargs)
    except Exception as exc:
        logger.exception("Background job failed: kind=%s job_id=%s", kind, job_id)
        job["status"] = "failed"
        job["error"] = str(exc)
    else:
        job["status"] = "succeeded"
        job["result"] = result
    finally:
        job["finished_at"] = asyncio.get_running_loop().time()


def _start_job(kind: str, func: Any, **kwargs: Any) -> dict[str, Any]:
    job_id = uuid.uuid4().hex[:12]
    JOB_STORE[job_id] = {
        "kind": kind,
        "status": "queued",
        "created_at": asyncio.get_running_loop().time(),
        "started_at": None,
        "finished_at": None,
        "error": None,
        "result": None,
    }
    asyncio.create_task(_run_job(job_id, kind, func, kwargs))
    return _job_public(job_id)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"request": request})


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
    return templates.TemplateResponse(request, "chat.html", context)


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
    return templates.TemplateResponse(request, "rag.html", context)


@app.get("/runs", response_class=HTMLResponse)
def runs_page(request: Request) -> HTMLResponse:
    summaries = _latest_run_summaries()
    return templates.TemplateResponse(request, "runs.html", {"request": request, "summaries": summaries})


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail_page(request: Request, run_id: str, offset: int = 0, limit: int = 100) -> HTMLResponse:
    detail = _load_run_detail(run_id, offset=offset, limit=limit)
    if detail is None:
        return templates.TemplateResponse(
            request,
            "run_detail.html",
            {
                "request": request,
                "run_id": run_id,
                "error": "Run not found",
                "summary": None,
                "results": [],
                "results_truncated": False,
                "preview_limit": limit,
                "offset": offset,
                "prev_offset": None,
                "next_offset": None,
            },
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "run_detail.html",
        {
            "request": request,
            "run_id": run_id,
            "summary": detail["summary"],
            "results": detail["results"],
            "results_truncated": detail["results_truncated"],
            "preview_limit": detail["preview_limit"],
            "offset": detail["offset"],
            "prev_offset": detail["prev_offset"],
            "next_offset": detail["next_offset"],
            "error": None,
        },
    )


@app.post("/api/jobs/chat")
async def start_chat_job(request: Request) -> dict[str, Any]:
    payload = await request.json()
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return {"error": "prompt is required"}
    model = str(payload.get("model") or _recommended_model("chat") or "").strip()
    if not model:
        return {"error": "No chat model is installed. Try `ollama pull llama3`."}
    job = _start_job(
        "chat",
        OllamaClient().chat_generate,
        model=model,
        prompt=prompt,
        temperature=float(payload.get("temperature", 0.2)),
        num_ctx=int(payload.get("num_ctx", 4096)),
    )
    return job


@app.post("/api/jobs/rag")
async def start_rag_job(request: Request) -> dict[str, Any]:
    payload = await request.json()
    question = str(payload.get("question", "")).strip()
    if not question:
        return {"error": "question is required"}
    chat_model = str(payload.get("model") or _recommended_model("rag_qa") or "").strip()
    embed_model = str(payload.get("embed_model") or _recommended_model("embeddings") or "").strip()
    if not chat_model:
        return {"error": "No RAG chat model installed. Try `ollama pull llama3`."}
    if not embed_model:
        return {"error": "No embeddings model installed. Try `ollama pull nomic-embed-text`."}
    job = _start_job(
        "rag",
        answer_question,
        question=question,
        index_dir=str(payload.get("index_dir", "runs/index")),
        chat_model_name=chat_model,
        embed_model_name=embed_model,
        k=int(payload.get("k", 5)),
        temperature=float(payload.get("temperature", 0.2)),
        num_ctx=int(payload.get("num_ctx", 4096)),
    )
    return job


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> dict[str, Any]:
    if job_id not in JOB_STORE:
        return {"error": "job not found", "job_id": job_id}
    return _job_public(job_id)
