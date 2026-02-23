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

version_help_output="$("${LUDWIG_BIN}" --help 2>&1 || true)"
version_line="$(printf '%s\n' "${version_help_output}" | grep -Eom1 'ludwig v[0-9]+(\.[0-9]+)*')"
if [[ -n "${version_line}" ]]; then
  echo "[ludwig] Detected version: ${version_line}"
  if [[ -n "${LUDWIG_EXPECTED_VERSION}" && "${version_line}" != *"${LUDWIG_EXPECTED_VERSION}"* ]]; then
    echo "[ludwig] Warning: this helper is configured for Ludwig ${LUDWIG_EXPECTED_VERSION}." >&2
  fi
fi

experiment_help=""
for help_flag in --help -h; do
  if experiment_help="$("${LUDWIG_BIN}" experiment "${help_flag}" 2>&1)"; then
    break
  fi
  # Some CLI variants print help to stderr and still return non-zero.
  if [[ -n "${experiment_help}" && ( "${experiment_help}" == *"usage:"* || "${experiment_help}" == *"--config"* ) ]]; then
    break
  fi
done
if [[ -z "${experiment_help}" ]]; then
  echo "[ludwig] Failed to inspect 'ludwig experiment --help'. Check your Ludwig install." >&2
  exit 1
fi
if [[ "${experiment_help}" != *"--config"* ]]; then
  echo "[ludwig] This Ludwig CLI variant does not advertise '--config' for 'experiment'." >&2
  echo "[ludwig] Captured 'ludwig experiment --help' output:" >&2
  printf '%s\n' "${experiment_help}" >&2
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
