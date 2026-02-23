# Operator's Guide

> Audience: local LLM lab operator (after the repo is built).
> If you are preparing a Codex prompt-run environment before `PROMPT_00_s.txt`, use `PROMPT_EXECUTION_OPERATORS_GUIDE.md` instead.

This guide covers the concrete steps to get the local LLM lab running on macOS with Ollama.

## 1) Install required tools (Homebrew)

```bash
brew install ollama uv ruff git jq ripgrep fd fzf
```

## 2) Start Ollama

Use one of:

```bash
brew services start ollama
```

or

```bash
ollama serve
```

## 3) Pull a minimal starter set of models

```bash
ollama pull llama3
ollama pull nomic-embed-text
```

Pull only what you need first. This helps preserve local storage.

## 4) Install Python with `uv` (if needed)

```bash
uv python install 3.12
```

## 5) Sync the project environment

```bash
uv sync --locked
```

If you intentionally changed `pyproject.toml`, update the lockfile first:

```bash
uv lock
uv sync --locked
```

This repo also includes a `.python-version` pinned to `3.12`, and the bootstrap script uses `uv sync --python 3.12 --locked` for reproducibility.

## 6) Baseline verification commands

```bash
uv run lab doctor
uv run lab models status
uv run lab models recommend --task chat
uv run lab models recommend --task embeddings
```

## 7) Minimal chat smoke test

```bash
uv run lab chat --prompt "hello"
```

## 8) Build and test retrieval

```bash
uv run lab ingest --corpus data/corpus --index runs/index
uv run lab retrieve --index runs/index --query "What is RAG?" --k 5
uv run lab rag --index runs/index --question "What command should an operator run first?"
```

## 9) Run the baseline evaluation harness

```bash
uv run lab run --config experiments/rag_baseline.yaml
uv run lab report --run runs/<run_id>
```

## 10) Optional web UI

```bash
uv run lab web --port 8000
```

Then open: `http://127.0.0.1:8000`

## 11) Optional Ludwig workflows (isolated environment)

Keep Ludwig in a separate venv so the main lab environment and lockfile remain stable:
Default helper target: `ludwig==0.10.4` on Python 3.12.

```bash
uv venv .venv-ludwig --python 3.12
uv pip install --python .venv-ludwig/bin/python "ludwig==0.10.4"
./scripts/run_ludwig_prompting.sh
```

If you intentionally install legacy `ludwig==0.7.5`, use Python 3.11 for that isolated venv.
