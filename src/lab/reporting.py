from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson
from rich.console import Console
from rich.table import Table


console = Console()


def _load_summary(run_dir: str | Path) -> dict[str, Any]:
    path = Path(run_dir) / "summary.json"
    return orjson.loads(path.read_bytes())


def print_run_summary(run_dir: str | Path) -> None:
    summary = _load_summary(run_dir)

    table = Table(title=f"Run Summary: {summary['run_id']}")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("config_name", str(summary["config_name"]))
    table.add_row("models", ", ".join(summary["models"]))
    table.add_row("embed_model", str(summary.get("embed_model")))
    table.add_row("question_count", str(summary["question_count"]))
    table.add_row("overall_accuracy_proxy", str(summary["aggregate_scores"]["overall"]["accuracy_proxy"]))
    table.add_row("overall_avg_latency_ms", str(summary["latency_stats"]["overall"]["avg_ms"]))
    console.print(table)

    model_table = Table(title="Per-model Metrics")
    model_table.add_column("Model", style="bold")
    model_table.add_column("Accuracy Proxy")
    model_table.add_column("Avg Latency (ms)")
    for model in summary["models"]:
        score = summary["aggregate_scores"]["per_model"][model]["accuracy_proxy"]
        avg_latency = summary["latency_stats"]["per_model"][model]["avg_ms"]
        model_table.add_row(model, str(score), str(avg_latency))
    console.print(model_table)


def compare_runs(run_dirs: list[str | Path]) -> None:
    summaries = [_load_summary(run_dir) for run_dir in run_dirs]
    table = Table(title="Run Comparison")
    table.add_column("Run ID", style="bold")
    table.add_column("Config")
    table.add_column("Models")
    table.add_column("Overall Accuracy Proxy")
    table.add_column("Overall Avg Latency (ms)")
    for summary in summaries:
        table.add_row(
            summary["run_id"],
            str(summary["config_name"]),
            ", ".join(summary["models"]),
            str(summary["aggregate_scores"]["overall"]["accuracy_proxy"]),
            str(summary["latency_stats"]["overall"]["avg_ms"]),
        )
    console.print(table)

