#!/usr/bin/env bash
set -euo pipefail

LUDWIG_VENV=".venv-ludwig"
LUDWIG_BIN="${LUDWIG_VENV}/bin/ludwig"

if [[ ! -x "${LUDWIG_BIN}" ]]; then
  echo "[ludwig] Ludwig is not installed in the isolated Ludwig environment (${LUDWIG_VENV})."
  echo "[ludwig] Create a separate Ludwig env so the main lab lockfile stays stable:"
  echo "  uv venv ${LUDWIG_VENV} --python 3.12"
  echo "  uv pip install --python ${LUDWIG_VENV}/bin/python 'ludwig==0.7.5'"
  exit 0
fi

echo "[ludwig] Running Ludwig prompting workflow with local dataset..."
echo "[ludwig] Config: ludwig/prompting.yaml"

version_output="$("${LUDWIG_BIN}" --version 2>&1 || true)"
if [[ -n "${version_output}" ]]; then
  echo "[ludwig] Detected version: ${version_output}"
  if [[ "${version_output}" != *"0.7.5"* ]]; then
    echo "[ludwig] Warning: this helper is documented/tested against Ludwig 0.7.5." >&2
  fi
fi

if ! experiment_help="$("${LUDWIG_BIN}" experiment --help 2>&1)"; then
  echo "[ludwig] Failed to inspect 'ludwig experiment --help'. Check your Ludwig install." >&2
  exit 1
fi
if [[ "${experiment_help}" != *"--config"* ]]; then
  echo "[ludwig] This Ludwig CLI variant does not advertise '--config' for 'experiment'." >&2
  echo "[ludwig] Verify the command syntax for your version before running." >&2
  exit 1
fi

if "${LUDWIG_BIN}" experiment --config ludwig/prompting.yaml; then
  echo "[ludwig] Prompting workflow completed."
else
  echo "[ludwig] Ludwig command failed. Verify Ludwig CLI syntax for your installed version." >&2
  exit 1
fi
