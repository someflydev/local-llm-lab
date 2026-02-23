#!/usr/bin/env bash
set -euo pipefail

echo "[verify] Running doctor..."
uv run lab doctor

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

