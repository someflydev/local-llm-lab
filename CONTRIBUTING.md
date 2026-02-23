# Contributing

Thanks for improving `local-llm-lab`. This repo is intentionally local-first and prompt-driven, so small, verifiable changes are preferred over broad refactors.

## Development Workflow

### Setup

Use the repo scripts and `uv`-managed Python:

```bash
./scripts/bootstrap_mac.sh
```

For deterministic local checks (no live Ollama required):

```bash
make check
make smoke-fixture
```

Optional live runtime smoke (gated):

```bash
LAB_LIVE_OLLAMA_SMOKE=1 ./scripts/live_ollama_smoke.sh
```

### Repo Layout (where changes belong)

- `src/lab/` — application code (CLI, RAG, runner, web, profiling)
- `tests/` — unit + integration smoke/edge tests
- `scripts/` — local operator and maintenance scripts
- `experiments/` — experiment configs + model policy
- `data/` — small local corpora/datasets/fixtures used by the repo
- `docs/` — operator/model/perf/deep-dive docs
- `schemas/` — generated JSON schemas for stable run artifacts (Stage-2+)
- `.prompts/` — prompt plan, manifests, and preflight/audit logs

## Testing

Run the same baseline checks CI uses:

```bash
uv run --python 3.12 --with ruff ruff check .
uv run --python 3.12 python -m unittest discover -s tests
```

Useful targeted runs:

```bash
uv run --python 3.12 python -m unittest tests.test_integration_basics tests.test_web_smoke
uv run --python 3.12 python -m unittest tests.test_integration_edge_cases tests.test_script_smoke
bash -n scripts/*.sh
./scripts/run_ludwig_prompting.sh --check-only
```

## Prompt Changes

Prompt files in `.prompts/` are the build plan. Treat prompt edits like code:

- Preserve intent and scope; prefer minimal clarifications over rewrites.
- Keep filenames ordered and zero-padded (`PROMPT_XX.txt`).
- If multiple prompts touch the same artifact, add explicit “extend, don’t overwrite” language.
- Update manifests (`.prompts/PROMPT_MANIFEST.md`, stage manifests) when adding or renumbering prompts.
- Add or update preflight notes when prompt sequencing or acceptance criteria change.

## Release Prep

Use the local release-prep checker before tagging:

```bash
./scripts/release_prep.sh --check
```

During prompt execution or while iterating on changes (dirty working tree), use:

```bash
./scripts/release_prep.sh --check --allow-dirty
```
