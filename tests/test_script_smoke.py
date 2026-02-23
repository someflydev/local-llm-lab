from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


class ScriptSmokeTests(unittest.TestCase):
    def test_bash_syntax_for_scripts(self) -> None:
        scripts = sorted(str(path) for path in (ROOT / "scripts").glob("*.sh"))
        self.assertTrue(scripts, "Expected shell scripts under scripts/")
        proc = _run(["bash", "-n", *scripts])
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)

    def test_ludwig_helper_check_only_is_non_failing(self) -> None:
        proc = _run(["./scripts/run_ludwig_prompting.sh", "--check-only"])
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        combined = f"{proc.stdout}\n{proc.stderr}"
        self.assertIn("[ludwig]", combined)

    def test_live_ollama_smoke_wrapper_help_if_present(self) -> None:
        script = ROOT / "scripts" / "live_ollama_smoke.sh"
        if not script.exists():
            self.skipTest("live_ollama_smoke.sh not present (PROMPT_12 may not have run)")
        proc = _run([str(script), "--help"])
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        self.assertIn("LAB_LIVE_OLLAMA_SMOKE", proc.stdout)


if __name__ == "__main__":
    unittest.main()

