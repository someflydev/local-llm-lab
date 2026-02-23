from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Any

import orjson
from langchain_ollama import OllamaEmbeddings


def _index_db_path(index_dir: str | Path) -> Path:
    return Path(index_dir) / "index.sqlite"


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Embedding vectors must have the same length")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve(
    query: str,
    k: int = 5,
    index_dir: str | Path = "runs/index",
    embed_model_name: str | None = None,
) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("query must not be empty")
    if k <= 0:
        raise ValueError("k must be > 0")
    if not embed_model_name:
        raise ValueError("embed_model_name is required for query embedding")

    db_path = _index_db_path(index_dir)
    if not db_path.exists():
        raise FileNotFoundError(f"Index database not found: {db_path}")

    embedder = OllamaEmbeddings(model=embed_model_name)
    query_vec = embedder.embed_query(query)

    rows: list[tuple[str, int, str, str]] = []
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT path, chunk_id, text, embedding FROM chunks").fetchall()

    scored: list[dict[str, Any]] = []
    for path, chunk_id, text, embedding_json in rows:
        emb = orjson.loads(embedding_json)
        score = _cosine_similarity(query_vec, emb)
        snippet = " ".join(text.split())[:220]
        scored.append(
            {
                "path": path,
                "chunk_id": chunk_id,
                "score": score,
                "snippet": snippet,
                "full_text": text,
            }
        )

    return sorted(scored, key=lambda item: item["score"], reverse=True)[:k]

