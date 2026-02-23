#!/usr/bin/env bash
set -euo pipefail

if ! uv run python -c "import ludwig" >/dev/null 2>&1; then
  echo "[ludwig] Ludwig is not installed in this environment."
  echo "[ludwig] Install the optional extra with:"
  echo "  uv sync --extra ludwig"
  exit 0
fi

echo "[ludwig] Running Ludwig prompting workflow with local dataset..."
echo "[ludwig] Config: ludwig/prompting.yaml"

if uv run ludwig experiment --config ludwig/prompting.yaml; then
  echo "[ludwig] Prompting workflow completed."
else
  echo "[ludwig] Ludwig command failed. Verify Ludwig CLI syntax for your installed version." >&2
  exit 1
fi

