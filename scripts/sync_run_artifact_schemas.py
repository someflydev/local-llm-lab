from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lab.run_artifact_models import run_result_row_schema, run_summary_schema


SCHEMA_DIR = Path("schemas")
SCHEMA_FILES = {
    SCHEMA_DIR / "run_summary.schema.json": run_summary_schema,
    SCHEMA_DIR / "run_result_row.schema.json": run_result_row_schema,
}


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def write_schemas() -> list[Path]:
    written: list[Path] = []
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for path, builder in SCHEMA_FILES.items():
        path.write_text(_canonical_json(builder()), encoding="utf-8")
        written.append(path)
    return written


def check_schemas() -> tuple[bool, list[Path]]:
    drifted: list[Path] = []
    for path, builder in SCHEMA_FILES.items():
        expected = _canonical_json(builder())
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            drifted.append(path)
    return (len(drifted) == 0), drifted


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate/check JSON Schemas for run artifacts.")
    parser.add_argument("--write", action="store_true", help="Write/update checked-in schema files.")
    parser.add_argument("--check", action="store_true", help="Fail if checked-in schemas drift.")
    args = parser.parse_args()

    if not args.write and not args.check:
        parser.error("Specify at least one of --write or --check")

    if args.write:
        paths = write_schemas()
        for path in paths:
            print(f"[schema-sync] wrote {path.as_posix()}")

    if args.check:
        ok, drifted = check_schemas()
        if not ok:
            print("[schema-sync] Schema drift detected:")
            for path in drifted:
                print(f"- {path.as_posix()}")
            print("[schema-sync] Run: python scripts/sync_run_artifact_schemas.py --write")
            return 1
        print("[schema-sync] Schemas are in sync.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

