# Prompt Execution Operator’s Guide (do this before starting PROMPT_00_s.txt)

> Audience: prompt-execution operator. This file is for preparing the machine before running the `.prompts/` sequence.
> If you want to operate the built local LLM lab itself, use `docs/operators_guide.md`.

## 0) Goals

You want a machine state where a Codex session can immediately:
- run ollama locally,
- create a Python project with uv,
- lint/format with ruff,
- build and run a local lab (CLI + RAG + eval + profiling + optional web UI).

## 1) Required Homebrew installs

Run:

```
brew update

# core runtime + python project tooling
brew install ollama uv ruff

# quality-of-life tools that help a lot in Codex sessions
brew install git jq ripgrep fd fzf

# optional but often useful for local dev ergonomics
brew install watch tree
```

## 2) Start Ollama (choose one)

Option A: foreground (simple):

```
ollama serve
```

Option B: background service (recommended):

```
brew services start ollama
```

Verify: 

```
ollama --version
ollama list
```

If `ollama list` is empty, that's OK.

## 3) Pull the minimum model set (recommended for your storage: ~115 GB free)

Start with just these:

```
ollama pull llama3
ollama pull nomic-embed-text
```

Why:

- **llama3** is your stable default chat/RAG QA model.
- **nomic-embed-text** is a common small/fast embeddings model for RAG.

(You can add more later, but don’t start by hoarding models.)

## 4) Make sure uv can manage Python

Pick a Python version and let uv manage it (3.12 is a great default):

```
uv python install 3.12
uv python list
```

(uv supports installing and switching Python versions.)
