# Post-Flight Report
## 1. Repo Summary (What it is, what it promises, how to run)

This repository is a local-first LLM experimentation lab centered on Ollama, with a Python CLI (`lab`), local RAG tooling, a lightweight experiment harness, a minimal FastAPI/Jinja web UI, profiling utilities, and documentation for optional Ludwig workflows.

What it promises (from `.prompts/PROMPT_00_s.txt` and implemented artifacts):
- Local chat + environment diagnostics (`src/lab/cli.py:24`, `src/lab/doctor.py:34`)
- Policy-driven model recommendations (`experiments/models.yaml`, `src/lab/model_registry.py:79`)
- Local embeddings ingestion/retrieval using sqlite + cosine similarity (`src/lab/ingest.py:22`, `src/lab/retrieval.py:27`)
- RAG QA with citations/refusal + eval harness (`src/lab/rag.py:48`, `src/lab/runner.py:109`)
- Profiling and optional web UI (`src/lab/profile.py:14`, `src/lab/web/app.py:19`)
- Broad operator/end-user docs (`README.md:1`, `docs/*.md`)

How to run locally (verified paths/commands exist):
- Bootstrap: `scripts/bootstrap_mac.sh` (`scripts/bootstrap_mac.sh:1`)
- Verify: `scripts/verify.sh` (`scripts/verify.sh:1`)
- CLI entrypoint: `lab` console script (`pyproject.toml:25`)
- Web UI: `uv run lab web --port 8000` (`src/lab/cli.py:402`)

High-level inventory (filesystem-verified):
- Python package: `src/lab/` (CLI, doctor, model registry, ingest/retrieval, RAG, runner, reporting, profiling)
- Web frontend assets: `src/lab/web/` + 6 templates in `src/lab/web/templates/`
- Data: `data/corpus/` (10 markdown files), `data/rag_eval_questions.jsonl`, `data/prompts/profile_prompt.txt`, `data/ludwig/prompting.jsonl`
- Experiment configs: `experiments/models.yaml`, `experiments/rag_baseline.yaml`, `experiments/rag_compare_models.yaml`
- Ludwig configs/templates: `ludwig/*.yaml`
- Docs: `README.md`, `docs/` (7 docs)
- Runtime artifacts (example outputs): `runs/` includes ingest metadata, logs, profile log, and a completed baseline eval run (`runs/20260223T015121Z_rag_baseline/summary.json`)

Primary entrypoints (code-level):
- CLI `main`: `src/lab/cli.py:422`
- FastAPI app: `src/lab/web/app.py:19`
- Web server launcher via CLI: `src/lab/cli.py:303`

Build signals / local runtime requirements:
- Python packaging: `uv` + `pyproject.toml` + `uv.lock` (`pyproject.toml:1`, `uv.lock`)
- Runtime service: local Ollama (`src/lab/doctor.py:40`, `src/lab/ollama_client.py`)
- Linting: Ruff (`pyproject.toml:34`)
- Optional Ludwig extra: `[project.optional-dependencies]` (`pyproject.toml:28`)
- No dedicated demo mode/fixture mode found. Closest equivalents are the bundled corpus/eval datasets and checked-in example `runs/` outputs.

Tests / CI / schemas (inventory check):
- Tests: no `tests/` directory and no test modules found in repo inventory
- CI: no `.github/workflows/*` files found
- Schemas/specs: no standalone JSON Schema/OpenAPI file artifacts found (FastAPI would generate OpenAPI at runtime, but no exported spec is checked in)

## 2. Prompt Intent Map (compressed)

Prompt Intent Map (Prompt ID -> goals -> promised artifacts -> implied dependencies)

- `PROMPT_00_s.txt`
  - Goal: define repo mission, constraints, and quality bar for a local LLM lab.
  - Promised artifacts: none directly (system-level constraints).
  - Dependencies implied: all later prompts must preserve local-only operation, Ollama runtime, uv/ruff workflow, hardware-aware defaults, and cumulative CLI behavior.

- `PROMPT_01.txt`
  - Goal: scaffold runnable repo baseline.
  - Promised artifacts: `pyproject.toml`, `uv.lock`, `.gitignore`, placeholder `README.md`, `src/lab/cli.py`, `src/lab/doctor.py`, `src/lab/ollama_client.py`, `src/lab/logging_jsonl.py`, `scripts/bootstrap_mac.sh`, `scripts/verify.sh`.
  - Dependencies implied: later prompts extend CLI, doctor, and package structure rather than replacing them.

- `PROMPT_02.txt`
  - Goal: model registry + recommendations.
  - Promised artifacts: `experiments/models.yaml`, `src/lab/modelspec.py`, `src/lab/model_registry.py`; CLI + doctor updates.
  - Dependencies implied: `PROMPT_03+` can default to policy-selected chat/embedding models.

- `PROMPT_03.txt`
  - Goal: local embeddings ingestion + retrieval without FAISS/Chroma.
  - Promised artifacts: 10-file corpus, `text_chunking.py`, `ingest.py`, `retrieval.py`; CLI `ingest`/`retrieve`.
  - Dependencies implied: `PROMPT_04` RAG pipeline and `PROMPT_05` runner depend on retrieval/index format.

- `PROMPT_04.txt`
  - Goal: full RAG QA pipeline with strict refusal + citations.
  - Promised artifacts: RAG prompt templates, `rag.py`, `data/rag_eval_questions.jsonl`; CLI `rag`; JSONL logging fields.
  - Dependencies implied: `PROMPT_05` eval harness reuses `answer_question`, refusal string, and dataset.

- `PROMPT_05.txt`
  - Goal: experiment harness and reporting.
  - Promised artifacts: `experiments/rag_baseline.yaml`, `experiments/rag_compare_models.yaml`, `runner.py`, `reporting.py`; CLI `run/report/compare`.
  - Dependencies implied: `PROMPT_06` web UI can read `summary.json` and `results.jsonl`.

- `PROMPT_06.txt`
  - Goal: minimal local web UI.
  - Promised artifacts: `src/lab/web/app.py`, template set, CLI `web`.
  - Dependencies implied: relies on existing CLI/RAG/runner outputs and installed web deps.

- `PROMPT_07.txt`
  - Goal: honest Ludwig integration on constrained hardware.
  - Promised artifacts: optional dependency setup, `docs/ludwig_workflows.md`, `data/ludwig/prompting.jsonl`, `ludwig/*.yaml`, `scripts/run_ludwig_prompting.sh`.
  - Dependencies implied: optional extra should not degrade core usability; docs should be explicit about feasibility.

- `PROMPT_08.txt`
  - Goal: model guidance and operator guide docs.
  - Promised artifacts: `docs/models.md`, `docs/operators_guide.md`.
  - Dependencies implied: docs must match model policy and CLI behavior.

- `PROMPT_09.txt`
  - Goal: profiling harness + perf docs.
  - Promised artifacts: `src/lab/profile.py`, `data/prompts/profile_prompt.txt`, `docs/perf.md`; CLI `profile`.
  - Dependencies implied: reuses existing chat generation path.

- `PROMPT_10.txt`
  - Goal: replace placeholder README with final README + beginner docs.
  - Promised artifacts: `README.md`, `docs/glossary.md`, `docs/rag_deep_dive.md`, `docs/neural_networks_101.md`.
  - Dependencies implied: docs should accurately reflect implemented CLI/features.

Scope / vision statement (extracted):
- A local Ollama-based LLM lab for chat, RAG, evaluation, profiling, optional web UI, and optional Ludwig workflows, optimized for M3 Pro 18GB-class constraints (`.prompts/PROMPT_00_s.txt`).

Constraints / non-goals (extracted):
- No external services required.
- Graceful degradation when models are missing.
- Conservative `num_ctx` defaults.
- No FAISS/Chroma requirement; pure-Python cosine similarity over sqlite for small corpora.

Quality bars called out in prompts:
- Runnable repo, not advice.
- Verification after milestones.
- Explicit assumptions/discovery.
- Cumulative CLI updates (added during preflight in `.prompts/improvements-before-initial-run.txt`).

Sequencing assumptions observed:
- CLI is incrementally extended across prompts 02/03/04/05/06/09 and depends on preserving prior subcommands.
- `PROMPT_05` runner assumes `PROMPT_03` ingest/retrieval and `PROMPT_04` RAG API contracts.
- `PROMPT_06` web run views assume `summary.json` + `results.jsonl` structure from `PROMPT_05`.
- `PROMPT_10` explicitly replaces the `PROMPT_01` placeholder README.

## 3. Traceability: Prompt -> Artifact Delivery Table

| Prompt ID | Intended artifacts | Found artifacts | Status | Notes | Suggested follow-up |
|---|---|---|---|---|---|
| `PROMPT_00_s.txt` | System-level constraints/vision only | N/A (guidance prompt), plus preflight log exists `.prompts/improvements-before-initial-run.txt` | Partial | Core scope is implemented, but quality-bar support artifacts (tests/CI/release hygiene) are missing | Add tests/CI and release metadata to better satisfy the system-level quality bar |
| `PROMPT_01.txt` | Baseline scaffold: `pyproject.toml`, `uv.lock`, `.gitignore`, placeholder README, CLI/doctor/client/logger, bootstrap/verify scripts | All present: `pyproject.toml`, `uv.lock`, `.gitignore`, `README.md`, `src/lab/*.py`, `scripts/*.sh` | Delivered | CLI/doctor/chat/models list exist and are integrated in `src/lab/cli.py` | Tighten bootstrap reproducibility (`uv sync --locked`, interpreter pinning) |
| `PROMPT_02.txt` | `experiments/models.yaml`, `modelspec.py`, `model_registry.py`, CLI status/recommend, doctor updates | All present and wired (`experiments/models.yaml`, `src/lab/modelspec.py`, `src/lab/model_registry.py`, `src/lab/cli.py`, `src/lab/doctor.py`) | Delivered | Policy buckets + recommendations exist; doctor prints hardware profile + storage advisory | Add tests for policy matching/recommendation rules |
| `PROMPT_03.txt` | Corpus (10 files), chunking, ingest, retrieval, CLI commands | `data/corpus/` has 10 files; `src/lab/text_chunking.py`, `ingest.py`, `retrieval.py`; CLI `ingest/retrieve` in `src/lab/cli.py` | Delivered | sqlite index format and pure-Python cosine scoring implemented | Add index schema migration/versioning or integrity checks |
| `PROMPT_04.txt` | RAG templates, `rag.py`, eval dataset, `lab rag`, logging fields | `src/lab/prompts/rag_*.txt`, `src/lab/rag.py`, `data/rag_eval_questions.jsonl`, CLI `rag`, JSONL logging via `lab.logging_jsonl` | Partial | Delivered, but `rag.py` adds hidden heuristic refusal normalization (`src/lab/rag.py:101`) that changes semantics from pure prompt-only behavior | Make heuristic optional/configurable and document it explicitly |
| `PROMPT_05.txt` | Experiment configs, runner, reporting, CLI run/report/compare | `experiments/rag_*.yaml`, `src/lab/runner.py`, `src/lab/reporting.py`, CLI subcommands exist | Delivered | Per-run index rebuild is implemented (`src/lab/runner.py:124`) and summary schema is emitted (`src/lab/runner.py:215`) | Add progress reporting/timeout controls for long eval runs |
| `PROMPT_06.txt` | FastAPI/Jinja UI + routes + CLI web | `src/lab/web/app.py`, 6 templates, `lab web` in CLI | Delivered | Root/chat/rag/runs/run detail routes exist; web startup dependency (`python-multipart`) is now included in `pyproject.toml:17` | Add JSON endpoints and async/non-blocking request handling for heavier usage |
| `PROMPT_07.txt` | Ludwig optional extra, docs, dataset, configs, runner script; at least one runnable flow if installed | `docs/ludwig_workflows.md`, `data/ludwig/prompting.jsonl` (60 rows), `ludwig/*.yaml`, `scripts/run_ludwig_prompting.sh`, optional extra in `pyproject.toml:28` | Partial | Optional integration exists, but successful Ludwig workflow execution is not provable from filesystem alone; helper script is version-sensitive (`scripts/run_ludwig_prompting.sh:14`) | Pin/test a known Ludwig version + command syntax in CI or add a compatibility matrix |
| `PROMPT_08.txt` | `docs/models.md`, `docs/operators_guide.md` | Both present | Delivered | Docs reflect model policy and operator steps (`docs/models.md`, `docs/operators_guide.md`) | Cross-link to root `OPERATORS_GUIDE.md` intent or rename one to avoid confusion |
| `PROMPT_09.txt` | `profile.py`, fixed prompt, perf docs, `lab profile` | `src/lab/profile.py`, `data/prompts/profile_prompt.txt`, `docs/perf.md`, CLI `profile` | Delivered | Logs to `runs/profile.jsonl` and prints per-run summary (`src/lab/profile.py:58`) | Add CSV export and percentile stats for longer runs |
| `PROMPT_10.txt` | Final README + glossary + beginner docs | `README.md`, `docs/glossary.md`, `docs/rag_deep_dive.md`, `docs/neural_networks_101.md` | Delivered | Placeholder README replaced and required sections/terms are present (`README.md:1`, `README.md:11`, `README.md:161`) | Add screenshots/GIFs and a release-quality examples section |

## 4. Completeness Score (0–100) + Rubric Breakdown

### Overall Completeness Score: **71 / 100**

This is a credible, runnable local LLM lab with real core workflows working end-to-end, but it is held back substantially by missing automated tests/CI, reproducibility rough edges, and optional-dependency lockfile blast radius.

### Rubric Breakdown

| Category | Score | Rationale (evidence) |
|---|---:|---|
| A) Core Functionality (0–25) | **22/25** | Core happy paths exist and have produced real outputs: chat/doctor/model policy/RAG/eval/profile/web (`src/lab/cli.py`, `runs/20260223T015121Z_rag_baseline/summary.json`, `runs/profile.jsonl`). Main missing points are reliability of RAG correctness and Ludwig runtime validation. |
| B) Developer Experience (0–20) | **16/20** | Clear `src/` layout, `uv`/`ruff` config, consolidated CLI, bootstrap/verify scripts, and broad docs (`pyproject.toml`, `scripts/*.sh`, `README.md`, `docs/`). Lost points for interpreter/reproducibility drift (`scripts/bootstrap_mac.sh:30-35`) and optional-extra lockfile churn. |
| C) Tests + Quality Gates (0–15) | **2/15** | No `tests/` and no CI workflows found. Quality validation is manual/interactive. |
| D) Docs + Examples (0–15) | **14/15** | Strong documentation coverage and examples across README, operator guide, models guide, perf notes, glossary, and beginner docs (`docs/` has 7 files). Loses a point for some quickstart/optional-extra packaging caveats not being front-and-center. |
| E) Operability + Safety (0–15) | **11/15** | Good CLI error handling, model fallbacks, JSONL logs, and structured run outputs (`src/lab/doctor.py`, `src/lab/logging_jsonl.py`, `src/lab/runner.py`). Loses points for long-running eval opacity/no timeout controls and hidden RAG heuristic behavior (`src/lab/rag.py:101-104`, `src/lab/runner.py:137-190`). |
| F) Packaging + Release Readiness (0–10) | **6/10** | Has package metadata, console script, and lockfile (`pyproject.toml`, `uv.lock`), but lacks license metadata/file, changelog/release checklist, and CI-based release confidence. |

Single biggest reason the score is not higher:
- **No automated tests/CI, combined with reproducibility drift in dependency management**, means the repo is runnable but not reliably maintainable/regression-resistant.

Single most leverage improvement to raise it fastest:
- **Add a small integration test suite + CI on pinned Python 3.12** covering `doctor` (mocked), model policy parsing, ingest/retrieve on fixture corpus, and one non-networked smoke path. This would materially improve score in both Tests and Developer Experience quickly.

## 5. General Excellence Rating (1–10) + Evidence

### General Excellence Rating: **7 / 10** (solid, credible project)

Evidence (factual, file-anchored):
- The repo has a coherent, purposeful architecture that maps cleanly to the prompt plan: policy -> ingest/retrieve -> RAG -> eval -> web -> profiling (`src/lab/*.py`, `experiments/*.yaml`, `src/lab/web/app.py`).
- The CLI is comprehensive and cohesive rather than fragmented (`src/lab/cli.py:335-419`).
- The model policy is explicit and hardware-aware, not hardcoded in scattered logic (`experiments/models.yaml`, `src/lab/model_registry.py:79`).
- The retrieval stack stays aligned with constraints (sqlite + cosine in Python, no FAISS/Chroma requirement) (`src/lab/retrieval.py:27-67`).
- Structured JSONL logging and run summaries make outputs inspectable and audit-friendly (`src/lab/logging_jsonl.py:15`, `src/lab/runner.py:215-237`).
- The project includes a real web UI and not just CLI/docs (`src/lab/web/app.py`, `src/lab/web/templates/*`).
- Documentation breadth is strong for a generated repo: operator, models, perf, Ludwig, glossary, RAG deep dive, neural nets 101 (`docs/`).
- Runtime artifacts show actual successful end-to-end usage, including a completed baseline eval and profile run (`runs/20260223T015121Z_rag_baseline/summary.json`, `runs/profile.jsonl`).
- Quality gates are mostly manual; there are no tests or CI, which sharply limits confidence for future changes (inventory: no `tests/`, no `.github/workflows/*`).
- Optional Ludwig support increases dependency/lock complexity significantly and mutates core package selections (e.g., `rich` pinned to older version in `uv.lock:2914-2924` due optional extra graph from `uv.lock:1401-1447`).
- Some behavior is hidden rather than explicit (RAG refusal threshold heuristic in `src/lab/rag.py:101-104`), which hurts trust/debuggability.
- Reproducibility messaging is inconsistent between docs and scripts (`docs/operators_guide.md:42-44` uses `uv sync --locked`, while `scripts/bootstrap_mac.sh:33-35` uses `uv sync`).

## 6. Priority Issues (P0–P3) (Prompt ID, Problem, Impact, Suggested Fix)

No confirmed P0 (core promise-breaking) issues were found in the current filesystem. The repo is usable and core flows are present.

| Issue ID | Priority | Prompt ID(s) | Problem | Evidence | Impact | Suggested Fix |
|---|---|---|---|---|---|---|
| PF-A01 | P1 | `PROMPT_00_s.txt` | No automated tests or CI despite a broad end-to-end surface area | No `tests/` directory or `.github/workflows/*` files in repo inventory; many commands and modules in `src/lab/cli.py:335-419` | Regressions are likely and hard to detect, especially across prompt-driven iterative changes | Add a minimal `tests/` suite + CI workflow (lint + unit + fixture-based integration tests) |
| PF-A02 | P1 | `PROMPT_01.txt`, `PROMPT_08.txt` | Bootstrap script uses unlocked dependency sync (`uv sync`) instead of `uv sync --locked` | `scripts/bootstrap_mac.sh:33-35` vs docs recommending `uv sync --locked` (`docs/operators_guide.md:42-44`) | New users can silently drift from the committed lockfile and get different dependency behavior | Change bootstrap to `uv sync --locked`; print explicit remediation if lock is stale |
| PF-A03 | P1 | `PROMPT_01.txt`, `PROMPT_07.txt` | Python interpreter reproducibility is not enforced; script installs 3.12 but does not ensure sync uses it | `scripts/bootstrap_mac.sh:30-35` installs Python 3.12 then runs plain `uv sync`; project only specifies `>=3.12` (`pyproject.toml:10`) | Users may sync under 3.14 and hit package compatibility/build issues (observed in practice during Ludwig lock/sync) | Add `.python-version` (3.12) and/or use `uv sync --python 3.12 --locked`; document supported interpreter(s) clearly |
| PF-A04 | P1 | `PROMPT_07.txt` | Optional Ludwig extra causes major lockfile blast radius and core dependency changes in the shared `uv.lock` | `pyproject.toml:28-29` optional extra + `uv.lock:1401-1447` (large Ludwig graph including torch stack) + `uv.lock:2914-2924` (`rich==12.4.4`) | Core CLI/web environment becomes harder to maintain and can pick older/transitive versions due optional extras | Split Ludwig into a separate project/env lock (`pyproject-ludwig.toml` or docs-only optional install strategy), or maintain a separate lockfile/environment for extras |
| PF-A05 | P1 | `PROMPT_04.txt`, `PROMPT_05.txt` | RAG path applies hidden score-threshold refusal normalization that can override model output | `src/lab/rag.py:101-104` | Can mask retrieval/prompt quality problems and skew eval results in non-obvious ways | Make threshold heuristic opt-in via config/flag and emit telemetry when triggered |
| PF-A06 | P2 | `PROMPT_05.txt` | Eval runner is long-running and silent with no progress output, cancellation handling, or per-question flush control | `src/lab/runner.py:137-190` writes results inside one buffered file handle and prints nothing until done | Poor operability for 20+ question runs; users may assume the process is hung | Print progress per question/model, flush after each line, and optionally add timeout/retry settings |
| PF-A07 | P2 | `PROMPT_04.txt`, `PROMPT_05.txt` | RAG citations are appended heuristically based on text inspection (`"chunk_id" not in answer_text`), mixing model output with post-processing | `src/lab/rag.py:109-113` | Makes evaluation and UX less predictable; answer text format changes implicitly | Return structured answer + citations separately and render citations in CLI/UI consistently without mutating answer text |
| PF-A08 | P2 | `PROMPT_06.txt` | Web handlers execute expensive local inference synchronously in request thread and swallow recommendation errors silently | `src/lab/web/app.py:59-63`, `src/lab/web/app.py:71-157` | UI responsiveness degrades under slow local inference; debugging failures is harder | Add explicit error surfaces/logging and consider async/background task pattern for long requests |
| PF-A09 | P3 | `PROMPT_06.txt` | Run detail page reads entire `results.jsonl` into memory before slicing first 100 rows | `src/lab/web/app.py:52-55` uses `read_text(...).splitlines()[:100]` | Inefficient for larger runs; unnecessary memory usage | Stream/iterate lines and stop after first N rows |
| PF-A10 | P3 | `PROMPT_08.txt` | Naming/docs duplication can confuse users: root `OPERATORS_GUIDE.md` (prompt-run prep) vs `docs/operators_guide.md` (product operator docs) | `OPERATORS_GUIDE.md:1` and `docs/operators_guide.md:1` | Users may read the wrong guide and get mixed expectations | Rename root file to `PROMPT_EXECUTION_OPERATORS_GUIDE.md` or add a banner clarifying audience/scope |
| PF-A11 | P3 | `PROMPT_07.txt` | Ludwig helper script relies on a version-sensitive CLI invocation without compatibility checks | `scripts/run_ludwig_prompting.sh:14-18` | Users may hit command syntax mismatch depending on Ludwig version | Pin a known Ludwig version and document/test the exact command; fallback to `uv run python -m ...` if CLI shape differs |
| PF-A12 | P3 | `PROMPT_10.txt` | README quickstart is strong but does not explicitly include model pulls before `lab chat`, despite optional/no-model state being common | `README.md:13-18` vs operator guide model pull step `docs/operators_guide.md:25-33` | New users may fail on `lab chat` immediately after quickstart if no models are installed | Add a quickstart note or branch: “If no model is installed, run `ollama pull llama3` and `ollama pull nomic-embed-text`” |

## 7. Overengineering / Complexity Risks (Complexity vs Value)

| Complexity hotspot | Risk | Value delivered | Simplification recommendation |
|---|---|---|---|
| Shared lockfile for core runtime + optional Ludwig graph (`uv.lock`) | High | Single lockfile convenience | Split Ludwig into separate env/lock or documented isolated workflow to protect core runtime stability |
| Ludwig optional integration breadth (docs + dataset + configs + script + heavy lock graph) | High | Signals ambition and optional extensibility | Keep docs/templates, but defer lockfile integration or maintain separate Ludwig workspace/branch |
| Hidden refusal heuristic in RAG path (`src/lab/rag.py`) | Med | Helps enforce refusal in some unsupported cases | Move to explicit config flag; default off in library, on in CLI if desired |
| CLI centralization in one large file (`src/lab/cli.py`) | Med | Single entrypoint is easy to discover | Keep one entrypoint but split command handlers into modules (e.g., `cli_models.py`, `cli_rag.py`) |
| Eval runner coupling to live inference + live ingest in a single function (`run_config`) | Med | Simple end-to-end execution path | Extract ingest phase / eval phase and add progress callbacks + timeout config |
| Web app directly calling inference functions in request handlers | Med | Fastest path to a working UI | Add thin service layer or JSON endpoints; keep templates simple |
| Documentation breadth in README + docs (some overlap) | Low | Great onboarding coverage | Reduce duplication and cross-link more (README short, docs deep) |
| Dual operator guides (root + docs) | Low | One for prompt execution, one for end users | Rename one and clarify intended audience at top |
| Results parsing in web detail page reads whole file | Low | Simpler code | Stream first N lines; add pagination later |
| Manual verification-driven workflow (scripts + docs, no tests) | High | Fast iteration during prompt execution | Convert existing verified commands into automated smoke tests and CI |

## 8. Naming / Structure / Consistency Findings

Findings (factual) and recommendations (separate):

- Factual: Directory layout matches the prompt plan well (`src/lab/`, `scripts/`, `data/`, `experiments/`, `ludwig/`, `docs/`).
  - Recommendation: Keep this layout stable and add a `CONTRIBUTING.md` that codifies where new artifacts belong.

- Factual: There are two operator guides with different audiences:
  - prompt-execution prep guide at `OPERATORS_GUIDE.md:1`
  - end-user product operator guide at `docs/operators_guide.md:1`
  - Recommendation: rename one or add an explicit audience banner to both files.

- Factual: The repo contains two prompt directories/namespaces that are easy to confuse:
  - execution prompts: `.prompts/`
  - RAG runtime prompt templates: `src/lab/prompts/`
  - Recommendation: keep `src/lab/prompts/` but rename README/docs references to “RAG prompt templates” when mentioning it.

- Factual: `runs/index/` (global/manual ingest) and `runs/<run_id>/index/` (experiment-local) are both used intentionally (`src/lab/ingest.py`, `src/lab/runner.py:119-130`).
  - Recommendation: document this distinction in README/operator guide to avoid accidental index reuse confusion.

- Factual: `scripts/bootstrap_mac.sh` and `docs/operators_guide.md` disagree on lockfile sync command (`uv sync` vs `uv sync --locked`).
  - Recommendation: standardize on `uv sync --locked` for all user-facing guidance/scripts.

- Factual: `pyproject.toml` lacks license metadata and the repo has no `LICENSE` file (inventory + `pyproject.toml:5-37`).
  - Recommendation: add license metadata/file before public distribution claims.

- Factual: No test directory or CI workflows are present.
  - Recommendation: establish `tests/` and `.github/workflows/ci.yml` before further feature expansion.

- Factual: Optional Ludwig support is represented in core `pyproject.toml` (`pyproject.toml:28-29`) and therefore in the shared `uv.lock`, materially changing lock contents (`uv.lock:1401-1447`, `uv.lock:2914-2924`).
  - Recommendation: isolate optional heavyweight paths to preserve baseline environment clarity.

## 9. Highest-Leverage Next Steps (Top 10) + Estimated Effort (S/M/L)

| Rank | Next step | Why it matters | Effort |
|---:|---|---|---|
| 1 | Add CI (`ruff`, import/syntax checks, fixture-based integration tests) | Biggest confidence gain; catches regressions immediately | M |
| 2 | Add `tests/` for model policy parsing, chunking, retrieval scoring, runner summary schema | Protects core logic and prompt-driven evolution | M |
| 3 | Make `scripts/bootstrap_mac.sh` use `uv sync --locked` and explicitly pin Python 3.12 | Improves reproducibility and aligns scripts/docs | S |
| 4 | Introduce `.python-version` (3.12) or equivalent uv interpreter pinning docs | Reduces Python-version drift and compatibility surprises | S |
| 5 | Isolate Ludwig optional environment/lock (or split project config) | Prevents heavy optional deps from destabilizing core runtime lockfile | M/L |
| 6 | Make RAG refusal heuristic configurable/off by default and log when it triggers | Improves transparency and eval trustworthiness | S/M |
| 7 | Add progress output + flush + optional timeouts to `lab run` | Major operability improvement for long eval runs | S/M |
| 8 | Add JSON API endpoints for runs/results and web-backed artifact explorer | Enables stronger frontend/productization without scraping templates | M |
| 9 | Add `LICENSE`, packaging metadata polish, and release checklist docs | Raises release readiness and external trust | S |
| 10 | Tighten README quickstart with explicit model-pull branching and screenshot/GIF proof points | Improves first-run success and front-facing conversion | S |
