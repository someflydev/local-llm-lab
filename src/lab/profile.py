from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

import orjson

from lab.ollama_client import OllamaClient


def profile(
    model: str,
    prompt_file: str | Path,
    n: int,
    num_ctx: int,
    temperature: float,
) -> dict[str, Any]:
    if n <= 0:
        raise ValueError("n must be > 0")

    prompt_path = Path(prompt_file)
    prompt_text = prompt_path.read_text(encoding="utf-8")

    client = OllamaClient(timeout_s=300.0)
    runs: list[dict[str, Any]] = []
    for i in range(n):
        started = time.perf_counter()
        result = client.chat_generate(
            model=model,
            prompt=prompt_text,
            temperature=temperature,
            num_ctx=num_ctx,
        )
        wall_ms = round((time.perf_counter() - started) * 1000, 2)
        text = result["text"]
        chars = len(text)
        chars_per_sec = round((chars / (wall_ms / 1000.0)) if wall_ms > 0 else 0.0, 2)
        runs.append(
            {
                "run_index": i + 1,
                "wall_ms": wall_ms,
                "latency_ms": result["latency_ms"],
                "chars": chars,
                "chars_per_sec": chars_per_sec,
            }
        )

    summary = {
        "model": model,
        "prompt_file": str(prompt_path),
        "n": n,
        "num_ctx": num_ctx,
        "temperature": temperature,
        "average_wall_ms": round(mean([r["wall_ms"] for r in runs]), 2),
        "average_chars_per_sec": round(mean([r["chars_per_sec"] for r in runs]), 2),
        "runs": runs,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    log_path = Path("runs") / "profile.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("ab") as fh:
        fh.write(orjson.dumps(summary))
        fh.write(b"\n")
    return summary

