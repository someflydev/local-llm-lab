# Operator's Guide

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

