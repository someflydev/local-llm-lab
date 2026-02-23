from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

import orjson
import yaml

from lab.ingest import ingest_corpus
from lab.model_registry import installed_models, recommend
from lab.rag import RAG_REFUSAL, answer_question


@dataclass
class RagEvalConfig:
    name: str
    task: str
    corpus_dir: str
    chat_models: list[str]
    embed_model: str
    k: int
    num_ctx: int
    temperature: float
    chunk_size_chars: int
    overlap_chars: int
    dataset_path: str
    refusal_score_threshold: float | None = None


def _load_config(path: str | Path) -> RagEvalConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return RagEvalConfig(**data)


def _load_dataset(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(orjson.loads(line))
    return rows


def _match_installed_name(policy_or_name: str, installed: set[str]) -> str | None:
    wanted = policy_or_name.lower()
    for name in sorted(installed):
        base = name.split(":", 1)[0].lower()
        if name.lower() == wanted or base == wanted:
            return name
    return None


def _resolve_embed_model(embed_model: str) -> str:
    if embed_model != "auto":
        return embed_model
    rec = recommend("embeddings")
    chosen = rec.get("chosen_model")
    if not chosen:
        pulls = ", ".join(rec.get("suggested_pulls", []))
        raise RuntimeError(f"No embeddings model available. Suggested pulls: {pulls or 'n/a'}")
    return str(chosen)


def _resolve_chat_models(chat_models: list[str]) -> list[str]:
    installed = installed_models()
    resolved: list[str] = []
    for item in chat_models:
        if item == "auto":
            rec = recommend("rag_qa")
            chosen = rec.get("chosen_model")
            if not chosen:
                pulls = ", ".join(rec.get("suggested_pulls", []))
                raise RuntimeError(f"No RAG chat model available. Suggested pulls: {pulls or 'n/a'}")
            resolved.append(str(chosen))
            continue
        match = _match_installed_name(item, installed)
        if not match:
            raise RuntimeError(f"Requested chat model not installed: {item}")
        resolved.append(match)
    return resolved


def _keyword_score(answer_text: str, expected_keywords: list[str]) -> tuple[int, int, int]:
    lowered = answer_text.lower()
    normalized_keywords = [kw.lower() for kw in expected_keywords]
    matched = sum(1 for kw in normalized_keywords if kw in lowered)
    if not normalized_keywords:
        return matched, 0, 0
    needed = len(normalized_keywords) if len(normalized_keywords) <= 2 else math.ceil(len(normalized_keywords) * 0.6)
    score = 1 if matched >= needed else 0
    return matched, needed, score


def _latency_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"count": 0, "avg_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0}
    return {
        "count": len(values),
        "avg_ms": round(mean(values), 2),
        "min_ms": round(min(values), 2),
        "max_ms": round(max(values), 2),
    }


def run_config(path: str | Path) -> Path:
    config_path = Path(path)
    cfg = _load_config(config_path)
    if cfg.task != "rag_eval":
        raise ValueError(f"Unsupported task: {cfg.task}")

    started_at = datetime.now(UTC)
    run_id = f"{started_at.strftime('%Y%m%dT%H%M%SZ')}_{cfg.name}"
    run_dir = Path("runs") / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    run_index_dir = run_dir / "index"

    embed_model = _resolve_embed_model(cfg.embed_model)
    chat_models = _resolve_chat_models(cfg.chat_models)

    ingest_corpus(
        corpus_dir=cfg.corpus_dir,
        index_dir=run_index_dir,
        embed_model_name=embed_model,
        chunk_size_chars=cfg.chunk_size_chars,
        overlap_chars=cfg.overlap_chars,
    )
    dataset = _load_dataset(cfg.dataset_path)
    total_tasks = len(dataset) * len(chat_models)
    print(
        f"[run] Starting run_id={run_id} questions={len(dataset)} models={len(chat_models)} "
        f"total_tasks={total_tasks}",
        flush=True,
    )

    results_path = run_dir / "results.jsonl"
    model_scores: dict[str, list[int]] = {model: [] for model in chat_models}
    model_latencies: dict[str, list[float]] = {model: [] for model in chat_models}
    task_num = 0

    with results_path.open("ab") as fh:
        for row in dataset:
            for model in chat_models:
                task_num += 1
                print(
                    f"[run] {task_num}/{total_tasks} question_id={row['id']} model={model}",
                    flush=True,
                )
                rag_result = answer_question(
                    question=row["question"],
                    index_dir=str(run_index_dir),
                    chat_model_name=model,
                    embed_model_name=embed_model,
                    k=cfg.k,
                    temperature=cfg.temperature,
                    num_ctx=cfg.num_ctx,
                    question_id=row["id"],
                    refusal_score_threshold=cfg.refusal_score_threshold,
                )
                answer_text = rag_result["answer_text"]
                if bool(row["answerable"]):
                    matched, needed, score = _keyword_score(answer_text, row["expected_keywords"])
                    score_reason = f"matched_keywords={matched}, needed={needed}"
                else:
                    score = 1 if answer_text.strip() == RAG_REFUSAL else 0
                    matched, needed = 0, 0
                    score_reason = "exact_refusal" if score == 1 else "missing_exact_refusal"

                record = {
                    "run_id": run_id,
                    "config_name": cfg.name,
                    "question_id": row["id"],
                    "question": row["question"],
                    "answerable": row["answerable"],
                    "model": model,
                    "embed_model": embed_model,
                    "k": cfg.k,
                    "num_ctx": cfg.num_ctx,
                    "temperature": cfg.temperature,
                    "answer_text": answer_text,
                    "citations": rag_result["citations"],
                    "retrieved": [
                        {
                            "path": item["path"],
                            "chunk_id": item["chunk_id"],
                            "score": item["score"],
                        }
                        for item in rag_result["retrieved"]
                    ],
                    "latency_ms": rag_result["latency_ms"],
                    "expected_keywords": row["expected_keywords"],
                    "matched_keywords": matched,
                    "needed_keywords": needed,
                    "score": score,
                    "score_reason": score_reason,
                }
                fh.write(orjson.dumps(record))
                fh.write(b"\n")
                fh.flush()
                model_scores[model].append(score)
                model_latencies[model].append(float(rag_result["latency_ms"]))

    finished_at = datetime.now(UTC)
    aggregate_scores = {
        "per_model": {
            model: {
                "total": sum(scores),
                "count": len(scores),
                "accuracy_proxy": round((sum(scores) / len(scores)), 4) if scores else 0.0,
            }
            for model, scores in model_scores.items()
        }
    }
    all_scores = [score for scores in model_scores.values() for score in scores]
    all_latencies = [lat for values in model_latencies.values() for lat in values]
    aggregate_scores["overall"] = {
        "total": sum(all_scores),
        "count": len(all_scores),
        "accuracy_proxy": round((sum(all_scores) / len(all_scores)), 4) if all_scores else 0.0,
    }
    latency_stats = {
        "overall": _latency_summary(all_latencies),
        "per_model": {model: _latency_summary(values) for model, values in model_latencies.items()},
    }

    summary = {
        "run_id": run_id,
        "config_name": cfg.name,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "corpus_dir": cfg.corpus_dir,
        "dataset_path": cfg.dataset_path,
        "models": chat_models,
        "embed_model": embed_model,
        "question_count": len(dataset),
        "aggregate_scores": aggregate_scores,
        "latency_stats": latency_stats,
        "config": {
            "k": cfg.k,
            "num_ctx": cfg.num_ctx,
            "temperature": cfg.temperature,
            "chunk_size_chars": cfg.chunk_size_chars,
            "overlap_chars": cfg.overlap_chars,
            "refusal_score_threshold": cfg.refusal_score_threshold,
        },
        "heuristic": "Answerable = keyword match (all if <=2 keywords else >=60%); unanswerable = exact refusal string.",
    }
    (run_dir / "summary.json").write_bytes(orjson.dumps(summary, option=orjson.OPT_INDENT_2))
    print(f"[run] Finished run_id={run_id}", flush=True)
    return run_dir
