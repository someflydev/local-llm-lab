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
- Python version pin file: `.python-version` (`.python-version`)
- Optional Ludwig workflow uses an isolated `.venv-ludwig` path (`docs/ludwig_workflows.md`, `scripts/run_ludwig_prompting.sh`)
- No dedicated demo mode/fixture mode found. Closest equivalents are the bundled corpus/eval datasets and checked-in example `runs/` outputs.

Tests / CI / schemas (inventory check):
- Tests: `tests/test_cli_parser.py`, `tests/test_rag_threshold.py`, `tests/test_integration_basics.py`, `tests/test_web_smoke.py` (8 `unittest` cases)
- CI: `.github/workflows/ci.yml` (locked sync + lint + `unittest discover`)
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
| `PROMPT_00_s.txt` | System-level constraints/vision only | N/A (guidance prompt), plus preflight log exists `.prompts/improvements-before-initial-run.txt` | Delivered | Core scope is implemented and now includes baseline tests + CI and reproducible bootstrap improvements | Add release hygiene (license/changelog) to further improve external readiness |
| `PROMPT_01.txt` | Baseline scaffold: `pyproject.toml`, `uv.lock`, `.gitignore`, placeholder README, CLI/doctor/client/logger, bootstrap/verify scripts | All present: `pyproject.toml`, `uv.lock`, `.gitignore`, `README.md`, `src/lab/*.py`, `scripts/*.sh` | Delivered | CLI/doctor/chat/models list exist and are integrated in `src/lab/cli.py`; bootstrap now uses locked Python 3.12 sync | Add shellcheck or script tests for bootstrap/verify scripts |
| `PROMPT_02.txt` | `experiments/models.yaml`, `modelspec.py`, `model_registry.py`, CLI status/recommend, doctor updates | All present and wired (`experiments/models.yaml`, `src/lab/modelspec.py`, `src/lab/model_registry.py`, `src/lab/cli.py`, `src/lab/doctor.py`) | Delivered | Policy buckets + recommendations exist; doctor prints hardware profile + storage advisory | Add tests for policy matching/recommendation rules |
| `PROMPT_03.txt` | Corpus (10 files), chunking, ingest, retrieval, CLI commands | `data/corpus/` has 10 files; `src/lab/text_chunking.py`, `ingest.py`, `retrieval.py`; CLI `ingest/retrieve` in `src/lab/cli.py` | Delivered | sqlite index format and pure-Python cosine scoring implemented | Add index schema migration/versioning or integrity checks |
| `PROMPT_04.txt` | RAG templates, `rag.py`, eval dataset, `lab rag`, logging fields | `src/lab/prompts/rag_*.txt`, `src/lab/rag.py`, `data/rag_eval_questions.jsonl`, CLI `rag`, JSONL logging via `lab.logging_jsonl` | Delivered | Refusal threshold heuristic is now explicit/optional via CLI flag and logged telemetry fields (`src/lab/cli.py`, `src/lab/rag.py`) | Add tests for citation rendering edge cases |
| `PROMPT_05.txt` | Experiment configs, runner, reporting, CLI run/report/compare | `experiments/rag_*.yaml`, `src/lab/runner.py`, `src/lab/reporting.py`, CLI subcommands exist | Delivered | Per-run index rebuild is implemented (`src/lab/runner.py:124`) and summary schema is emitted (`src/lab/runner.py:215`) | Add progress reporting/timeout controls for long eval runs |
| `PROMPT_06.txt` | FastAPI/Jinja UI + routes + CLI web | `src/lab/web/app.py`, 6 templates, `lab web` in CLI | Delivered | Root/chat/rag/runs/run detail routes exist; web startup dependency (`python-multipart`) is now included in `pyproject.toml:17` | Add JSON endpoints and async/non-blocking request handling for heavier usage |
| `PROMPT_07.txt` | Ludwig optional extra, docs, dataset, configs, runner script; at least one runnable flow if installed | `docs/ludwig_workflows.md`, `data/ludwig/prompting.jsonl` (60 rows), `ludwig/*.yaml`, `scripts/run_ludwig_prompting.sh` (isolated `.venv-ludwig` workflow) | Partial | Optional integration exists and is isolated from the core lockfile, but successful Ludwig workflow execution is not provable from filesystem alone | Add compatibility validation for the pinned Ludwig command/version path |
| `PROMPT_08.txt` | `docs/models.md`, `docs/operators_guide.md` | Both present | Delivered | Docs reflect model policy and operator steps (`docs/models.md`, `docs/operators_guide.md`) | Cross-link to root `OPERATORS_GUIDE.md` intent or rename one to avoid confusion |
| `PROMPT_09.txt` | `profile.py`, fixed prompt, perf docs, `lab profile` | `src/lab/profile.py`, `data/prompts/profile_prompt.txt`, `docs/perf.md`, CLI `profile` | Delivered | Logs to `runs/profile.jsonl` and prints per-run summary (`src/lab/profile.py:58`) | Add CSV export and percentile stats for longer runs |
| `PROMPT_10.txt` | Final README + glossary + beginner docs | `README.md`, `docs/glossary.md`, `docs/rag_deep_dive.md`, `docs/neural_networks_101.md` | Delivered | Placeholder README replaced and required sections/terms are present (`README.md:1`, `README.md:11`, `README.md:161`) | Add screenshots/GIFs and a release-quality examples section |

## 4. Completeness Score (0–100) + Rubric Breakdown

### Overall Completeness Score: **89 / 100**

This is a credible, runnable local LLM lab with real core workflows working end-to-end. Recent fixes materially improved reproducibility, operability, maintainability, and packaging readiness (tests, CI, fixture integration smoke tests, locked bootstrap sync, isolated Ludwig environment, explicit RAG heuristic control, runner progress output, web responsiveness fixes, license metadata/file), but a few operability and release-polish gaps still limit confidence.

### Rubric Breakdown

| Category | Score | Rationale (evidence) |
|---|---:|---|
| A) Core Functionality (0–25) | **22/25** | Core happy paths exist and have produced real outputs: chat/doctor/model policy/RAG/eval/profile/web (`src/lab/cli.py`, `runs/20260223T015121Z_rag_baseline/summary.json`, `runs/profile.jsonl`). Main missing points are reliability of RAG correctness and Ludwig runtime validation. |
| B) Developer Experience (0–20) | **18/20** | Clear `src/` layout, `uv`/`ruff` config, consolidated CLI, bootstrap/verify scripts, and broad docs, now with locked Python 3.12 bootstrap sync (`scripts/bootstrap_mac.sh:30-42`) and `.python-version`. Loses points for long-running command UX and manual Ludwig side-environment setup. |
| C) Tests + Quality Gates (0–15) | **12/15** | CI now runs lint + `unittest`, and the repo includes unit plus fixture-based integration smoke tests for ingest/retrieve/runner/web routes (`tests/test_integration_basics.py`, `tests/test_web_smoke.py`, `.github/workflows/ci.yml`). Coverage is still not fully end-to-end against live Ollama. |
| D) Docs + Examples (0–15) | **15/15** | Strong documentation coverage and examples across README, operator guide, models guide, perf notes, glossary, beginner docs, and updated Ludwig isolation guidance (`docs/` + `README.md`). |
| E) Operability + Safety (0–15) | **14/15** | Good CLI error handling, model fallbacks, JSONL logs, structured run outputs, explicit opt-in RAG refusal threshold telemetry, eval progress/flush output, and improved web error logging + `to_thread` offloading (`src/lab/rag.py:102-128`, `src/lab/runner.py:133-154`, `src/lab/web/app.py:76-82`, `src/lab/web/app.py:89-193`). Loses points for missing timeout/cancellation controls and lack of background-job handling for long web actions. |
| F) Packaging + Release Readiness (0–10) | **8/10** | Has package metadata, console script, lockfile, `.python-version`, CI, and a tracked license file/metadata (`pyproject.toml`, `LICENSE`, `.github/workflows/ci.yml`), but still lacks release checklist/changelog conventions and a declared distribution/release process. |

Single biggest reason the score is not higher:
- **Operability edge cases and release process polish are now the limiting factors**: the repo has a solid automated baseline, but long-running flows still lack timeout/background-job controls and release conventions are not defined.

Single most leverage improvement to raise it fastest:
- **Add timeout/cancellation controls to `lab run` and a background-job mode for longer web actions** to convert current usability into stronger operational reliability.

## 5. General Excellence Rating (1–10) + Evidence

### General Excellence Rating: **8 / 10** (solid, credible project with improving polish)

Evidence (factual, file-anchored):
- The repo has a coherent, purposeful architecture that maps cleanly to the prompt plan: policy -> ingest/retrieve -> RAG -> eval -> web -> profiling (`src/lab/*.py`, `experiments/*.yaml`, `src/lab/web/app.py`).
- The CLI is comprehensive and cohesive rather than fragmented (`src/lab/cli.py:335-419`).
- The model policy is explicit and hardware-aware, not hardcoded in scattered logic (`experiments/models.yaml`, `src/lab/model_registry.py:79`).
- The retrieval stack stays aligned with constraints (sqlite + cosine in Python, no FAISS/Chroma requirement) (`src/lab/retrieval.py:27-67`).
- Structured JSONL logging and run summaries make outputs inspectable and audit-friendly (`src/lab/logging_jsonl.py:15`, `src/lab/runner.py:215-237`).
- The project includes a real web UI and not just CLI/docs (`src/lab/web/app.py`, `src/lab/web/templates/*`).
- Documentation breadth is strong for a generated repo: operator, models, perf, Ludwig, glossary, RAG deep dive, neural nets 101 (`docs/`).
- Runtime artifacts show actual successful end-to-end usage, including a completed baseline eval and profile run (`runs/20260223T015121Z_rag_baseline/summary.json`, `runs/profile.jsonl`).
- A baseline quality gate now exists with CI and unit tests (`.github/workflows/ci.yml`, `tests/test_cli_parser.py`, `tests/test_rag_threshold.py`), improving maintainability.
- Ludwig guidance now uses an isolated `.venv-ludwig` workflow, reducing core lockfile blast radius (`docs/ludwig_workflows.md`, `scripts/run_ludwig_prompting.sh`).
- The RAG refusal score threshold is now explicit and opt-in, with telemetry logged when used (`src/lab/rag.py:102-132`, `src/lab/cli.py:389-396`, `src/lab/runner.py:31`, `src/lab/runner.py:150`).
- Reproducibility messaging is aligned between docs and bootstrap script via locked Python 3.12 sync (`scripts/bootstrap_mac.sh:34-42`, `docs/operators_guide.md`).
- `lab run` now emits per-question progress and flushes `results.jsonl` incrementally, improving long-run visibility and partial-result safety (`src/lab/runner.py:133-154`, `src/lab/runner.py:201-204`).
- The web UI now streams run-detail previews, surfaces recommendation warnings, logs request failures, and uses `asyncio.to_thread` for chat/RAG work (`src/lab/web/app.py:46-58`, `src/lab/web/app.py:89-193`).
- RAG answers no longer mutate `answer_text` to append citations; citations are rendered separately in CLI/UI (`src/lab/rag.py:112-114`, `src/lab/cli.py`, `src/lab/web/templates/rag.html`).
- The repo now includes fixture-based integration smoke tests for ingest/retrieve/runner summary generation and web routes, and they run in the local `unittest` suite (`tests/test_integration_basics.py`, `tests/test_web_smoke.py`).
- Packaging metadata now includes a tracked `LICENSE` file and `pyproject.toml` license metadata/classifiers (conservatively marked `UNLICENSED`) (`LICENSE`, `pyproject.toml`).

## 6. Priority Issues (P0–P3) (Prompt ID, Problem, Impact, Suggested Fix)

No confirmed P0, P1, or P2 issues were found in the current filesystem after the applied fixes. The repo is usable and core flows are present.

| Issue ID | Priority | Prompt ID(s) | Problem | Evidence | Impact | Suggested Fix |
|---|---|---|---|---|---|---|
| PF-A06 | P3 | `PROMPT_05.txt` | `lab run` now shows progress and flushes results, but still lacks timeout/cancellation/retry controls for long or stalled model calls | `src/lab/runner.py:133-154`, `src/lab/runner.py:201-204` | Long evaluations are more observable now, but a single stalled request can still block the run | Add per-call timeout/retry settings (configurable) and graceful interruption handling |
| PF-A08 | P3 | `PROMPT_06.txt` | Web UI now logs failures and offloads work with `asyncio.to_thread`, but long-running actions still execute inline with no background job/progress model | `src/lab/web/app.py:89-193` | UI requests can still time out or feel stuck during heavy local inference/eval actions | Add optional background job endpoints + polling for long-running operations |
| PF-A09 | P3 | `PROMPT_06.txt` | Run detail now streams a preview, but there is still no pagination/filtering for large `results.jsonl` files | `src/lab/web/app.py:46-58`, `src/lab/web/templates/run_detail.html` | Operators can inspect a preview quickly, but deeper run inspection still requires manual file access | Add pagination/filter controls (server-side line windowing) for run detail |
| PF-A10 | P3 | `PROMPT_08.txt` | Dual operator-guide naming remains potentially confusing even after audience banners were added | `OPERATORS_GUIDE.md:1-4`, `docs/operators_guide.md:1-4` | Banners reduce confusion, but similar filenames still increase onboarding ambiguity | Consider renaming the root guide to `PROMPT_EXECUTION_OPERATORS_GUIDE.md` |
| PF-A11 | P3 | `PROMPT_07.txt` | Ludwig helper now validates version/syntax locally, but compatibility is still not CI-verified | `scripts/run_ludwig_prompting.sh:18-34`, `docs/ludwig_workflows.md:48-54` | Optional workflow remains version-fragile across environments | Add an optional/stubbed compatibility smoke check in CI or a checked-in tested-version matrix sample |
| PF-A15 | P3 | `PROMPT_10.txt` | Release process conventions are still undocumented (no changelog or release checklist) | Repo inventory (no `CHANGELOG.md`, no release docs) | Harder to publish repeatable releases despite stronger code quality and packaging metadata | Add a lightweight `RELEASE_CHECKLIST.md` and simple changelog convention |

## 7. Overengineering / Complexity Risks (Complexity vs Value)

| Complexity hotspot | Risk | Value delivered | Simplification recommendation |
|---|---|---|---|
| Ludwig integration remains a separate environment with manual setup (`docs/ludwig_workflows.md`, `scripts/run_ludwig_prompting.sh`) | Med | Preserves optional capability while protecting the core lockfile | Keep isolated env approach; add lightweight CI verification or a maintained compatibility matrix |
| Ludwig optional integration breadth (docs + dataset + configs + script) | Med | Signals ambition and optional extensibility | Keep docs/templates, but postpone deeper automation until demand is proven |
| Long-running eval calls still lack timeout/cancellation controls (`src/lab/runner.py`) | Med | Simple runner implementation and deterministic loop | Add configurable timeout/retry/cancel handling while preserving current summary schema |
| CLI centralization in one large file (`src/lab/cli.py`) | Med | Single entrypoint is easy to discover | Keep one entrypoint but split command handlers into modules (e.g., `cli_models.py`, `cli_rag.py`) |
| Eval runner coupling to live inference + live ingest in a single function (`run_config`) | Med | Simple end-to-end execution path | Extract ingest phase / eval phase and add progress callbacks + timeout config |
| Web app directly calling inference functions in request handlers | Med | Fastest path to a working UI | Add thin service layer or JSON endpoints; keep templates simple |
| Documentation breadth in README + docs (some overlap) | Low | Great onboarding coverage | Reduce duplication and cross-link more (README short, docs deep) |
| Dual operator guides (root + docs) with similar filenames | Low | One for prompt execution, one for end users | Keep audience banners; optionally rename the root guide for stronger distinction |
| Run detail preview is streamed but not pageable | Low | Fast initial load for large runs | Add pagination/filtering when run sizes grow |
| Live-Ollama/runtime validation is still mostly manual (tests are mocked/fixture-based) | Med | Fast, deterministic CI without local model dependencies | Add optional gated live-smoke tests for local environments and nightly/manual CI jobs |

## 8. Naming / Structure / Consistency Findings

Findings (factual) and recommendations (separate):

- Factual: Directory layout matches the prompt plan well (`src/lab/`, `scripts/`, `data/`, `experiments/`, `ludwig/`, `docs/`).
  - Recommendation: Keep this layout stable and add a `CONTRIBUTING.md` that codifies where new artifacts belong.

- Factual: There are two operator guides with different audiences, and both now include audience banners:
  - prompt-execution prep guide at `OPERATORS_GUIDE.md:1`
  - end-user product operator guide at `docs/operators_guide.md:1`
  - Recommendation: current banners are sufficient for now; rename the root guide later if onboarding confusion persists.

- Factual: The repo contains two prompt directories/namespaces that are easy to confuse:
  - execution prompts: `.prompts/`
  - RAG runtime prompt templates: `src/lab/prompts/`
  - Recommendation: keep `src/lab/prompts/` but rename README/docs references to “RAG prompt templates” when mentioning it.

- Factual: `runs/index/` (global/manual ingest) and `runs/<run_id>/index/` (experiment-local) are both used intentionally (`src/lab/ingest.py`, `src/lab/runner.py:119-130`).
  - Recommendation: document this distinction in README/operator guide to avoid accidental index reuse confusion.

- Factual: `scripts/bootstrap_mac.sh` and `docs/operators_guide.md` are aligned on locked sync and Python 3.12 guidance.
  - Recommendation: keep this alignment and add shell-level checks (or `shellcheck`) to prevent drift.

- Factual: The repo now includes a tracked `LICENSE` file and conservative `UNLICENSED` metadata/classifier entries in `pyproject.toml`.
  - Recommendation: if you intend to open-source the repo later, replace `UNLICENSED` with an explicit license (for example MIT/Apache-2.0) and update metadata consistently.

- Factual: The test suite now includes unit tests plus fixture-based integration smoke tests for ingest/retrieve/runner/web routes, and CI runs them.
  - Recommendation: next expand coverage toward live-Ollama optional smoke tests (gated) and more edge-case assertions.

- Factual: Optional Ludwig support is now documented as an isolated `.venv-ludwig` workflow and no longer lives in core `pyproject.toml`.
  - Recommendation: keep the isolated workflow and add a version compatibility note/test to reduce operator guesswork.

## 9. Highest-Leverage Next Steps (Top 10) + Estimated Effort (S/M/L)

| Rank | Next step | Why it matters | Effort |
|---:|---|---|---|
| 1 | Add per-call timeout/retry/cancellation controls to `lab run` | Completes the runner operability story beyond progress+flush | S/M |
| 2 | Add background-job + polling support for long web actions (optional mode) | Prevents UI stalls and improves observability for heavier use | M |
| 3 | Add `RELEASE_CHECKLIST.md` and a simple changelog convention | Completes release process polish now that license/CI are in place | S |
| 4 | Add JSON API endpoints for runs/results and web-backed artifact explorer | Enables stronger frontend/productization without scraping templates | M |
| 5 | Add run-detail pagination/filtering for large `results.jsonl` files | Improves inspection ergonomics at scale | S/M |
| 6 | Add a Ludwig compatibility smoke check (optional/stubbed) or richer tested-version matrix | Reduces operator friction for the optional path | S/M |
| 7 | Expand integration tests with additional edge cases (index integrity, malformed rows, web error paths) | Builds confidence without requiring live Ollama | M |
| 8 | Add `shellcheck` (or shell smoke tests) for bootstrap/verify helper scripts | Prevents script/docs drift regressions | S |
| 9 | Consider renaming root `OPERATORS_GUIDE.md` if users still confuse it with `docs/operators_guide.md` | Improves onboarding clarity | S |
| 10 | Add screenshots/GIF proof points + CI badge to README/front-facing packaging | Improves evaluator confidence and conversion | S |
