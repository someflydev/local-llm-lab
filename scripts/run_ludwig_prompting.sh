#!/usr/bin/env bash
set -euo pipefail

LUDWIG_VENV="${LUDWIG_VENV:-.venv-ludwig}"
LUDWIG_BIN="${LUDWIG_BIN:-${LUDWIG_VENV}/bin/ludwig}"
LUDWIG_PYTHON_VERSION="${LUDWIG_PYTHON_VERSION:-3.12}"
LUDWIG_EXPECTED_VERSION="${LUDWIG_EXPECTED_VERSION:-0.10.4}"
CHECK_ONLY=0

if [[ "${1:-}" == "--check-only" ]]; then
  CHECK_ONLY=1
fi

if [[ ! -x "${LUDWIG_BIN}" ]]; then
  echo "[ludwig] Ludwig is not installed in the isolated Ludwig environment (${LUDWIG_VENV})."
  echo "[ludwig] Create a separate Ludwig env so the main lab lockfile stays stable:"
  echo "  uv venv ${LUDWIG_VENV} --python ${LUDWIG_PYTHON_VERSION}"
  echo "  uv pip install --python ${LUDWIG_VENV}/bin/python 'ludwig==${LUDWIG_EXPECTED_VERSION}'"
  if [[ ${CHECK_ONLY} -eq 1 ]]; then
    echo "[ludwig] Check-only mode: skipping because isolated Ludwig env is not installed."
  fi
  exit 0
fi

echo "[ludwig] Running Ludwig prompting workflow with local dataset..."
echo "[ludwig] Config: ludwig/prompting.yaml"

version_output="$("${LUDWIG_BIN}" --version 2>&1 || true)"
if [[ -n "${version_output}" ]]; then
  echo "[ludwig] Detected version: ${version_output}"
  if [[ -n "${LUDWIG_EXPECTED_VERSION}" && "${version_output}" != *"${LUDWIG_EXPECTED_VERSION}"* ]]; then
    echo "[ludwig] Warning: this helper is configured for Ludwig ${LUDWIG_EXPECTED_VERSION}." >&2
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

if [[ ${CHECK_ONLY} -eq 1 ]]; then
  echo "[ludwig] Check-only mode: version/syntax validation passed."
  exit 0
fi

if "${LUDWIG_BIN}" experiment --config ludwig/prompting.yaml; then
  echo "[ludwig] Prompting workflow completed."
else
  echo "[ludwig] Ludwig command failed. Verify Ludwig CLI syntax for your installed version." >&2
  exit 1
fi
