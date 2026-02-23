from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

from lab.run_artifact_models import RunResultRow, RunSummary


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_RUN = ROOT / "tests" / "fixtures" / "run_artifacts" / "sample_run"


def _run_python_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


class RunArtifactSchemaTests(unittest.TestCase):
    def test_models_validate_fixture_files(self) -> None:
        summary = json.loads((FIXTURE_RUN / "summary.json").read_text(encoding="utf-8"))
        RunSummary.model_validate(summary)

        first_line = (FIXTURE_RUN / "results.jsonl").read_text(encoding="utf-8").splitlines()[0]
        row = json.loads(first_line)
        RunResultRow.model_validate(row)

    def test_model_rejects_missing_required_field(self) -> None:
        summary = json.loads((FIXTURE_RUN / "summary.json").read_text(encoding="utf-8"))
        summary.pop("run_id", None)
        with self.assertRaises(ValidationError):
            RunSummary.model_validate(summary)

    def test_schema_sync_write_then_check(self) -> None:
        write_proc = _run_python_script("scripts/sync_run_artifact_schemas.py", "--write")
        self.assertEqual(write_proc.returncode, 0, msg=write_proc.stderr or write_proc.stdout)
        check_proc = _run_python_script("scripts/sync_run_artifact_schemas.py", "--check")
        self.assertEqual(check_proc.returncode, 0, msg=check_proc.stderr or check_proc.stdout)
        self.assertIn("Schemas are in sync", check_proc.stdout)

    def test_validate_run_artifacts_fixture(self) -> None:
        proc = _run_python_script(
            "scripts/validate_run_artifacts.py",
            "--run-dir",
            str(FIXTURE_RUN),
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        self.assertIn("[validate-run-artifacts] OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()

