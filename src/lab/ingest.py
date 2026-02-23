from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson
from langchain_ollama import OllamaEmbeddings

from lab.text_chunking import chunk_text


def _sorted_corpus_files(corpus_dir: Path) -> list[Path]:
    return sorted([p for p in corpus_dir.rglob("*.md") if p.is_file()])


def _index_db_path(index_dir: str | Path) -> Path:
    return Path(index_dir) / "index.sqlite"


def ingest_corpus(
    corpus_dir: str | Path,
    index_dir: str | Path,
    embed_model_name: str,
    chunk_size_chars: int = 900,
    overlap_chars: int = 120,
) -> dict[str, Any]:
    corpus_path = Path(corpus_dir)
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_path}")

    files = _sorted_corpus_files(corpus_path)
    if not files:
        raise ValueError(f"No markdown files found under {corpus_path}")

    records: list[dict[str, Any]] = []
    texts: list[str] = []
    for doc_num, path in enumerate(files, start=1):
        content = path.read_text(encoding="utf-8")
        chunks = chunk_text(content, chunk_size_chars=chunk_size_chars, overlap_chars=overlap_chars)
        rel_path = str(path.as_posix())
        for chunk_id, chunk in enumerate(chunks):
            records.append(
                {
                    "doc_id": f"doc-{doc_num:03d}",
                    "path": rel_path,
                    "chunk_id": chunk_id,
                    "text": chunk,
                }
            )
            texts.append(chunk)

    if not texts:
        raise ValueError("Corpus contained no chunkable text")

    embedder = OllamaEmbeddings(model=embed_model_name)
    vectors = embedder.embed_documents(texts)
    if len(vectors) != len(records):
        raise RuntimeError("Embedding count did not match chunk count")

    db_path = _index_db_path(index_dir)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE chunks (
                doc_id TEXT NOT NULL,
                path TEXT NOT NULL,
                chunk_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                embedding TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            "INSERT INTO chunks (doc_id, path, chunk_id, text, embedding) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    rec["doc_id"],
                    rec["path"],
                    rec["chunk_id"],
                    rec["text"],
                    orjson.dumps(vec).decode("utf-8"),
                )
                for rec, vec in zip(records, vectors, strict=True)
            ],
        )
        conn.commit()

    metadata = {
        "embedding_model": embed_model_name,
        "file_count": len(files),
        "chunk_count": len(records),
        "chunk_params": {
            "chunk_size_chars": chunk_size_chars,
            "overlap_chars": overlap_chars,
        },
        "timestamp": datetime.now(UTC).isoformat(),
        "index_db_path": str(db_path.as_posix()),
    }
    metadata_path = Path("runs") / "ingest.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_bytes(orjson.dumps(metadata, option=orjson.OPT_INDENT_2))
    return metadata

