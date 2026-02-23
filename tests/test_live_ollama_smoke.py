from __future__ import annotations

import os
import subprocess
import unittest


def _env_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


class LiveOllamaSmokeTests(unittest.TestCase):
    def _strict(self) -> bool:
        return _env_enabled("LAB_LIVE_OLLAMA_SMOKE_STRICT")

    def _run_lab(self, *args: str) -> subprocess.CompletedProcess[str]:
        timeout = float(os.getenv("LAB_LIVE_OLLAMA_TIMEOUT_SECS", "45"))
        return subprocess.run(
            ["uv", "run", "--python", "3.12", "lab", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    def _skip_or_fail(self, message: str, proc: subprocess.CompletedProcess[str] | None = None) -> None:
        details = ""
        if proc is not None:
            details = (
                f"\nexit_code={proc.returncode}\n"
                f"stdout:\n{proc.stdout.strip()}\n"
                f"stderr:\n{proc.stderr.strip()}"
            )
        if self._strict():
            self.fail(message + details)
        self.skipTest(message + details)

    def test_live_ollama_cli_happy_path(self) -> None:
        if not _env_enabled("LAB_LIVE_OLLAMA_SMOKE"):
            self.skipTest("Set LAB_LIVE_OLLAMA_SMOKE=1 to enable live Ollama smoke tests.")

        doctor = self._run_lab("doctor")
        if doctor.returncode != 0:
            self._skip_or_fail("lab doctor did not pass (Ollama may be unreachable).", doctor)

        models_list = self._run_lab("models", "list")
        if models_list.returncode != 0:
            self._skip_or_fail("lab models list failed.", models_list)

        models = []
        for line in models_list.stdout.splitlines():
            line = line.strip()
            if line.startswith("- "):
                models.append(line[2:].strip())
        if not models:
            self._skip_or_fail("No local models installed for live smoke test.", models_list)

        model_name = next((name for name in models if name.startswith("llama3")), models[0])

        chat = self._run_lab("chat", "--model", model_name, "--prompt", "Say hello in five words.")
        if chat.returncode != 0:
            self._skip_or_fail(f"lab chat failed for model {model_name}.", chat)

        self.assertTrue(chat.stdout.strip(), "Expected non-empty stdout from lab chat")
        self.assertIn("Model:", chat.stdout)


if __name__ == "__main__":
    unittest.main()

