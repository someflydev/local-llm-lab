from __future__ import annotations

import subprocess
import time
from typing import Any

import httpx


def parse_ollama_list_output(output: str) -> list[str]:
    """Parse `ollama list` output into model names."""
    models: list[str] = []
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return models

    # Typical output has a header row with "NAME".
    for line in lines:
        if line.lower().startswith("name"):
            continue
        first_col = line.split()[0]
        if first_col:
            models.append(first_col)
    return models


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout_s: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def list_models(self) -> list[str]:
        # Prefer HTTP API, fallback to CLI parsing.
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
            models = [item["name"] for item in data.get("models", []) if item.get("name")]
            if models:
                return models
        except Exception:
            pass

        proc = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "Failed to run `ollama list`")
        return parse_ollama_list_output(proc.stdout)

    def chat_generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        num_ctx: int = 4096,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        payload = {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": temperature, "num_ctx": num_ctx},
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            resp = client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        message = data.get("message") or {}
        text = (message.get("content") or "").strip()
        raw_snippet = str(data)[:500]
        return {"text": text, "latency_ms": latency_ms, "raw_response_snippet": raw_snippet}

