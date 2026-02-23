#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/verify.sh [--doctor-only] [--help]

Runs a local verification flow:
1) lab doctor
2) lab models list
3) one-shot chat if a model is available

Options:
  --doctor-only  Stop after `lab doctor`
  --help         Show this help
EOF
}

DOCTOR_ONLY=0
case "${1:-}" in
  --help|-h)
    usage
    exit 0
    ;;
  --doctor-only)
    DOCTOR_ONLY=1
    ;;
  "")
    ;;
  *)
    echo "[verify] Unknown argument: ${1}" >&2
    usage >&2
    exit 2
    ;;
esac

echo "[verify] Running doctor..."
uv run lab doctor

if [[ ${DOCTOR_ONLY} -eq 1 ]]; then
  echo "[verify] Doctor-only mode complete."
  exit 0
fi

echo "[verify] Listing models..."
models_output="$(uv run lab models list || true)"
echo "$models_output"

model_name=""
if echo "$models_output" | grep -E '^- ' | grep -q '^-\s*llama3'; then
  model_name="$(echo "$models_output" | grep -E '^- ' | sed 's/^- //' | grep '^llama3' | head -n1)"
else
  model_name="$(echo "$models_output" | grep -E '^- ' | sed 's/^- //' | head -n1 || true)"
fi

if [[ -z "${model_name}" ]]; then
  echo "[verify] WARNING: No models installed. Recommended: ollama pull llama3"
  exit 0
fi

echo "[verify] Running one-shot inference with model: ${model_name}"
uv run lab chat --model "${model_name}" --prompt "Say hello from the local LLM lab in one sentence."
