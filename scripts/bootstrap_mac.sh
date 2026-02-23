#!/usr/bin/env bash
set -euo pipefail

REQUIRED_BREW_PKGS=(ollama uv ruff git jq ripgrep fd fzf)

echo "[bootstrap] Checking Homebrew packages..."
missing=()
for pkg in "${REQUIRED_BREW_PKGS[@]}"; do
  if ! brew list --versions "$pkg" >/dev/null 2>&1; then
    missing+=("$pkg")
  fi
done

if ((${#missing[@]} > 0)); then
  echo "[bootstrap] Missing brew packages: ${missing[*]}"
  echo "[bootstrap] Install them first, e.g.: brew install ${missing[*]}"
else
  echo "[bootstrap] All required brew packages are installed."
fi

echo "[bootstrap] Checking Ollama HTTP endpoint..."
if curl -sf http://127.0.0.1:11434/api/tags >/dev/null; then
  echo "[bootstrap] Ollama appears to be running."
else
  echo "[bootstrap] Ollama is not reachable at http://127.0.0.1:11434"
  echo "[bootstrap] Start it with: brew services start ollama"
  echo "[bootstrap] Or run foreground server: ollama serve"
fi

echo "[bootstrap] Ensuring Python 3.12 via uv (idempotent)..."
uv python install 3.12

echo "[bootstrap] Syncing project dependencies..."
if ! uv sync --python 3.12 --locked; then
  echo "[bootstrap] Locked sync failed."
  echo "[bootstrap] If you intentionally changed dependencies, run:"
  echo "  uv lock && uv sync --python 3.12 --locked"
  exit 1
fi

echo "[bootstrap] Running doctor..."
uv run --python 3.12 lab doctor
