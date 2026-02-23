#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/live_ollama_smoke.sh [--help]

Runs the optional gated live Ollama smoke test.

Environment:
  LAB_LIVE_OLLAMA_SMOKE=1         Enable the live smoke unittest
  LAB_LIVE_OLLAMA_SMOKE_STRICT=1  Fail instead of skip if Ollama/models are unavailable
  LAB_LIVE_OLLAMA_TIMEOUT_SECS=45 Per-command timeout (seconds)

Notes:
  - Exits 0 when the test is skipped (default behavior if prerequisites are missing).
  - Uses the `lab` CLI codepath (doctor/models/chat), not raw HTTP-only checks.
EOF
}

case "${1:-}" in
  --help|-h)
    usage
    exit 0
    ;;
  "")
    ;;
  *)
    echo "[live-smoke] Unknown argument: ${1}" >&2
    usage >&2
    exit 2
    ;;
esac

if [[ "${LAB_LIVE_OLLAMA_SMOKE:-0}" != "1" ]]; then
  echo "[live-smoke] LAB_LIVE_OLLAMA_SMOKE is not set to 1. Running anyway; test should skip."
  echo "[live-smoke] To force live execution: LAB_LIVE_OLLAMA_SMOKE=1 ./scripts/live_ollama_smoke.sh"
fi

echo "[live-smoke] Running tests.test_live_ollama_smoke ..."
uv run --python 3.12 python -m unittest tests.test_live_ollama_smoke

