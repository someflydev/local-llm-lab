from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass

import httpx
from rich.console import Console
from rich.table import Table

from lab.modelspec import get_hardware_profile
from lab.ollama_client import parse_ollama_list_output


console = Console()


@dataclass
class CheckResult:
    name: str
    status: str  # PASS | WARN | FAIL
    detail: str


def _run_cmd(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    output = (proc.stdout or "").strip()
    if not output:
        output = (proc.stderr or "").strip()
    return proc.returncode, output


def run_doctor(base_url: str = "http://127.0.0.1:11434") -> int:
    results: list[CheckResult] = []

    system = platform.system()
    if system == "Darwin":
        results.append(CheckResult("platform", "PASS", f"macOS detected ({platform.platform()})"))
    else:
        results.append(CheckResult("platform", "WARN", f"Expected macOS; detected {platform.platform()}"))

    code, out = _run_cmd(["uv", "--version"])
    results.append(CheckResult("uv", "PASS" if code == 0 else "FAIL", out or "no output"))

    code, out = _run_cmd(["ollama", "--version"])
    results.append(CheckResult("ollama_cli", "PASS" if code == 0 else "FAIL", out or "no output"))

    try:
        profile = get_hardware_profile()
        results.append(
            CheckResult(
                "hardware_profile",
                "PASS",
                (
                    "mac_m3_pro_18gb_sonoma_14_5 "
                    f"(safe num_ctx={profile.safe_default_num_ctx}, cautious max={profile.cautious_max_num_ctx}, "
                    f"recommended class={profile.recommended_max_class})"
                ),
            )
        )
    except Exception as exc:
        results.append(CheckResult("hardware_profile", "WARN", f"Could not load experiments/models.yaml: {exc}"))

    free_storage_override = os.getenv("FREE_STORAGE_GB")
    if free_storage_override:
        try:
            free_storage_gb = float(free_storage_override)
            status = "WARN" if free_storage_gb < 30 else "PASS"
            detail = f"FREE_STORAGE_GB override={free_storage_gb:g} GB"
            if status == "WARN":
                detail += " (tight for multiple local model pulls; prune unused models)"
            results.append(CheckResult("free_storage", status, detail))
        except ValueError:
            results.append(CheckResult("free_storage", "WARN", f"Invalid FREE_STORAGE_GB value: {free_storage_override!r}"))
    else:
        results.append(
            CheckResult(
                "free_storage",
                "WARN",
                "Free storage not auto-detected. Set FREE_STORAGE_GB to enable an advisory check.",
            )
        )

    ollama_http_ok = False
    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=5.0)
        resp.raise_for_status()
        model_count = len((resp.json() or {}).get("models", []))
        results.append(CheckResult("ollama_http", "PASS", f"reachable at {base_url} ({model_count} models)"))
        ollama_http_ok = True
    except Exception as exc:
        results.append(CheckResult("ollama_http", "FAIL", f"unreachable at {base_url}: {exc}"))

    code, out = _run_cmd(["ollama", "list"])
    if code == 0:
        models = parse_ollama_list_output(out)
        if models:
            if any(name.startswith("llama3") for name in models):
                detail = f"{len(models)} model(s) installed; llama3 detected and will be preferred"
                results.append(CheckResult("ollama_models", "PASS", detail))
            else:
                detail = (
                    f"{len(models)} model(s) installed; llama3 not found. "
                    "Recommended: `ollama pull llama3`"
                )
                results.append(CheckResult("ollama_models", "WARN", detail))
        else:
            results.append(
                CheckResult("ollama_models", "WARN", "No models installed. Recommended: `ollama pull llama3`")
            )
    else:
        status = "FAIL" if not ollama_http_ok else "WARN"
        results.append(CheckResult("ollama_models", status, out or "Failed to run `ollama list`"))

    table = Table(title="Local LLM Lab Doctor")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Details")
    for r in results:
        color = {"PASS": "green", "WARN": "yellow", "FAIL": "red"}.get(r.status, "white")
        table.add_row(r.name, f"[{color}]{r.status}[/{color}]", r.detail)
    console.print(table)

    failed = any(r.status == "FAIL" for r in results)
    return 1 if failed else 0
