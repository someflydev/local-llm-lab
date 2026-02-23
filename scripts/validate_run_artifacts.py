from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from lab.run_artifact_models import RunResultRow, RunSummary


def _validate_run_dir(run_dir: Path) -> int:
    if not run_dir.exists():
        print(f"[validate-run-artifacts] Run dir not found: {run_dir}")
        print("[validate-run-artifacts] Provide a fixture path or an existing runs/<run_id> directory.")
        return 0
    if not run_dir.is_dir():
        print(f"[validate-run-artifacts] Not a directory: {run_dir}")
        return 1

    summary_path = run_dir / "summary.json"
    results_path = run_dir / "results.jsonl"
    if not summary_path.exists():
        print(f"[validate-run-artifacts] Missing summary file: {summary_path}")
        return 1
    if not results_path.exists():
        print(f"[validate-run-artifacts] Missing results file: {results_path}")
        return 1

    try:
        summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
        RunSummary.model_validate(summary_data)
    except (json.JSONDecodeError, ValidationError) as exc:
        print(f"[validate-run-artifacts] Summary validation failed: {exc}")
        return 1

    row_count = 0
    try:
        for line_num, line in enumerate(results_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            row_count += 1
            RunResultRow.model_validate(json.loads(line))
    except (json.JSONDecodeError, ValidationError) as exc:
        print(f"[validate-run-artifacts] Results row validation failed (line {line_num}): {exc}")
        return 1

    print(
        f"[validate-run-artifacts] OK: {run_dir.as_posix()} "
        f"(summary + {row_count} result row{'s' if row_count != 1 else ''})"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate run artifact files against pydantic models.")
    parser.add_argument("--run-dir", required=True, help="Path to a run directory containing summary.json/results.jsonl")
    args = parser.parse_args()
    return _validate_run_dir(Path(args.run_dir))


if __name__ == "__main__":
    raise SystemExit(main())

