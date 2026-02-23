# Prompt Manifest

This manifest tracks the intended execution order and dependency edges for the repo’s prompt-driven build pipeline.

## Stage 1 (Executed)

| Prompt ID | Type | Purpose (Compressed) | Primary Outputs / Areas | Depends On |
|---|---|---|---|---|
| `PROMPT_00_s.txt` | System | Global mission, stack, constraints, quality rules | Overall repo design and execution rules | — |
| `PROMPT_01.txt` | Task | Scaffold repo, CLI, doctor, chat, logging, bootstrap/verify scripts | `src/lab/`, `scripts/`, `pyproject.toml`, placeholder `README.md` | `PROMPT_00_s.txt` |
| `PROMPT_02.txt` | Task | Model registry + policy (`models.yaml`) + CLI model commands | `experiments/models.yaml`, `src/lab/model_registry.py` | `PROMPT_01.txt` |
| `PROMPT_03.txt` | Task | Corpus, chunking, ingest, retrieval, CLI commands | `data/corpus/`, `src/lab/ingest.py`, `src/lab/retrieval.py` | `PROMPT_02.txt` |
| `PROMPT_04.txt` | Task | RAG pipeline, prompts/templates, eval dataset | `src/lab/rag.py`, `src/lab/prompts/`, `data/rag_eval_questions.jsonl` | `PROMPT_03.txt` |
| `PROMPT_05.txt` | Task | Eval harness, reporting, experiment configs | `src/lab/runner.py`, `src/lab/reporting.py`, `experiments/rag_*.yaml` | `PROMPT_04.txt` |
| `PROMPT_06.txt` | Task | FastAPI/Jinja local web UI | `src/lab/web/` | `PROMPT_05.txt` |
| `PROMPT_07.txt` | Task | Ludwig optional workflows, configs, docs, script | `ludwig/`, `data/ludwig/`, `docs/ludwig_workflows.md`, helper script | `PROMPT_06.txt` |
| `PROMPT_08.txt` | Task | Model/operator documentation | `docs/models.md`, `docs/operators_guide.md` | `PROMPT_07.txt` |
| `PROMPT_09.txt` | Task | Profiling harness + perf docs | `src/lab/profile.py`, `docs/perf.md`, `data/prompts/profile_prompt.txt` | `PROMPT_08.txt` |
| `PROMPT_10.txt` | Task | Final README + glossary + beginner docs | `README.md`, `docs/glossary.md`, beginner docs | `PROMPT_09.txt` |

## Stage 2 (Planned)

| Prompt ID | Purpose (Compressed) | Primary Outputs / Areas | Depends On | Addresses |
|---|---|---|---|---|
| `PROMPT_11.txt` | Deterministic bring-up/check/teardown wiring | `Makefile`, script wrappers/docs links | Stage-1 audited repo | DX, reproducibility, operator safety |
| `PROMPT_12.txt` | Optional gated live-Ollama smoke tests | live smoke test, wrapper script, optional workflow, docs notes | `PROMPT_11.txt` recommended (not required) | Highest-leverage runtime confidence gap |
| `PROMPT_13.txt` | Integration edge cases + shell/script CI checks | new tests + `ci.yml` updates | `PROMPT_11.txt` recommended (not required) | deterministic regression coverage |
| `PROMPT_14.txt` | Contributor workflow + release hygiene automation | `CONTRIBUTING.md`, release prep script, docs links | none (can run anytime after Stage-1) | packaging/process excellence |
| `PROMPT_15.txt` | Lightweight run-artifact schemas + validation hooks | pydantic artifact models, `schemas/`, sync/validate scripts, tests | none (best after `PROMPT_13`) | automation compatibility checks |

## Sequencing Guidance
- Execute Stage-2 in numeric order unless a specific prompt is intentionally cherry-picked.
- If a prompt fails its acceptance criteria, stop and resolve before continuing (see `.prompts/PROMPT_STAGE2_MANIFEST.md`).
- Stage-2 explicitly excludes frontend/product-site work.

