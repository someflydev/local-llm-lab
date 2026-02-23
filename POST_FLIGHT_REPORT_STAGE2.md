# Post-Flight Report (Stage-2)

## 1. Executive Summary (what changed, what works now)

Stage-2 materially improved operational completeness and auditability without changing core product scope. The repo now has:

- a deterministic local operator layer (`Makefile`) for bring-up/check/smoke/cleanup/release checks (`Makefile:1`)
- optional gated live-Ollama smoke validation in a separate workflow (`tests/test_live_ollama_smoke.py:38`, `.github/workflows/live-ollama-smoke.yml:1`)
- stronger deterministic regression coverage (edge cases + script smoke) and expanded CI checks (`tests/test_integration_edge_cases.py:30`, `tests/test_script_smoke.py:22`, `.github/workflows/ci.yml:20`)
- release hygiene automation and contributor guidance (`scripts/release_prep.sh:1`, `CONTRIBUTING.md:1`, `RELEASE_CHECKLIST.md:7`)
- lightweight run-artifact schemas + validation hooks for automation compatibility (`src/lab/run_artifact_models.py:8`, `scripts/sync_run_artifact_schemas.py:11`, `scripts/validate_run_artifacts.py:12`, `schemas/run_summary.schema.json`)

What works now (verified in this audit run):
- `make check` passes (`ruff` + full `unittest`) with no live Ollama requirement
- full test suite passes with the gated live smoke test skipped by default (`23` tests, `1` skipped)
- targeted edge/script tests pass (`10` tests)
- strict `./scripts/release_prep.sh --check` passes on a clean tree
- schema sync check passes and real run-artifact validation passes

## 2. Scorecard (Completeness 0–100, Excellence 1–10) + Deltas

### Overall Scores

- **Completeness: 98 / 100** (Stage-1: `94 / 100`, delta `+4`)
- **General Excellence: 9 / 10** (Stage-1: `9 / 10`, delta `0`)

### Rubric Breakdown (re-run)

| Category | Stage-1 | Stage-2 | Delta | Evidence / Rationale |
|---|---:|---:|---:|---|
| A) Core Functionality (0–25) | 23 | **24** | +1 | Core features unchanged, but Stage-2 adds optional live-runtime validation via a gated smoke test and optional workflow (`tests/test_live_ollama_smoke.py:38`, `.github/workflows/live-ollama-smoke.yml:1`), increasing confidence in the real happy path. |
| B) Developer Experience (0–20) | 18 | **19** | +1 | Deterministic local commands and guardrails improved materially via `Makefile` + script UX (`Makefile:8`, `Makefile:14`, `Makefile:28`, `scripts/verify.sh:4`, `scripts/release_prep.sh:4`) plus `CONTRIBUTING.md` (`CONTRIBUTING.md:5`). |
| C) Tests + Quality Gates (0–15) | 12 | **15** | +3 | CI now validates shell syntax, script smoke behavior, schema sync drift, and the full suite (`.github/workflows/ci.yml:20-29`), and tests now include edge cases, live-smoke gating, script smoke, and schema validation (`tests/test_integration_edge_cases.py:30`, `tests/test_live_ollama_smoke.py:12`, `tests/test_script_smoke.py:22`, `tests/test_run_artifact_schemas.py:25`). |
| D) Docs + Examples (0–15) | 15 | **15** | 0 | Already strong in Stage-1; Stage-2 adds contributor/release docs and optional live smoke guidance but the category was already maxed (`CONTRIBUTING.md:1`, `RELEASE_CHECKLIST.md:1`, `README.md`). |
| E) Operability + Safety (0–15) | 15 | **15** | 0 | Stage-2 reinforces safety (guarded cleanup, strict/dirty-aware release checks, schema validation) but the category was already maxed in Stage-1 (`Makefile:46`, `scripts/release_prep.sh:101`, `scripts/validate_run_artifacts.py:12`). |
| F) Packaging + Release Readiness (0–10) | 9 | **10** | +1 | Release readiness baseline is now operationalized (not just documented) via `release_prep.sh`, `Makefile release-check`, schema drift checks, and `CONTRIBUTING.md` (`scripts/release_prep.sh:1`, `Makefile:63`, `.github/workflows/ci.yml:24`, `RELEASE_CHECKLIST.md:7`). |

### Score Delta (what moved the needle most)

Largest positive movement came from:
1. **CI/test gate depth increase**: shell syntax, script smoke, schema sync drift check, and new edge-case tests (`.github/workflows/ci.yml:20-29`, `tests/test_integration_edge_cases.py:30`).
2. **Deterministic operator flow**: `Makefile` targets unify common paths and add guarded cleanup/release checks (`Makefile:8-16`, `Makefile:28-66`).
3. **Release hygiene automation**: `scripts/release_prep.sh` converts release guidance into executable checks (`scripts/release_prep.sh:4-129`).
4. **Schema compatibility hooks**: generated schemas + validator improve artifact contract confidence (`src/lab/run_artifact_models.py:23`, `scripts/sync_run_artifact_schemas.py:22`, `scripts/validate_run_artifacts.py:12`).

Why excellence stayed at `9/10` (not `10/10`):
- Remaining gaps are mostly polish/packaging proof and optional-runtime operability details (for example, self-hosted runner provisioning for the live smoke workflow, front-facing proof assets still intentionally out of scope).

## 3. DoD-S2 Verification Table (Pass/Fail + Evidence)

Source of truth: `.prompts/PROMPT_STAGE2_MANIFEST.md:18-37`

| DoD-S2 item | Pass/Fail | Evidence (command/file) | Notes |
|---|---|---|---|
| `Makefile` provides `help`, `check`, `verify`, `smoke-fixture`, `clean-runs-preview`, `clean-runs` | **Pass** | `Makefile:6-66`; `make help` output (verified in audit) lists all required targets | Includes `release-check` bonus target (`Makefile:63`) |
| Deterministic local checks run without live Ollama (`make check`) | **Pass** | `Makefile:14-16`; audit run: `make check` exited `0` and ran `ruff` + `unittest` | Test suite result observed: `23` tests, `1` skipped (gated live smoke) |
| Optional live-Ollama smoke tests exist and are gated/skippable | **Pass** | `tests/test_live_ollama_smoke.py:38-66`, `scripts/live_ollama_smoke.sh:35-41`, `.github/workflows/live-ollama-smoke.yml:1-23` | Default `unittest discover` pass confirms skip path; separate optional workflow prevents CI instability |
| Default CI includes shell/script health checks and remains deterministic | **Pass** | `.github/workflows/ci.yml:20-29` | Default CI adds shell syntax + script smoke + schema sync checks; live Ollama smoke is separate (`.github/workflows/live-ollama-smoke.yml`) |
| Additional edge-case integration tests cover failure paths | **Pass** | `tests/test_integration_edge_cases.py:34-55`, `:57-104`, `:110-171`, `:177-218`, `:219-258`; `tests/test_script_smoke.py:23-41`; audit run of targeted tests exited `0` | Covers ingest/retrieve validation, runner retry/timeout/error summaries, malformed dataset row, web missing job/run + pagination clamp, script checks |
| Contributor workflow is documented | **Pass** | `CONTRIBUTING.md:1-80` | Includes setup, repo layout, testing, prompt changes, release prep |
| Release prep script validates repo readiness without mutating files | **Pass** | `scripts/release_prep.sh:10-20`, `:60-121`, `:123-129`; audit run `./scripts/release_prep.sh --check` exited `0` | Strict clean-tree check implemented (`scripts/release_prep.sh:101-109`) |
| Run artifact schema models + checked-in schemas exist and are sync-checkable | **Pass** | `src/lab/run_artifact_models.py:23-51`, `schemas/run_summary.schema.json`, `schemas/run_result_row.schema.json`, `scripts/sync_run_artifact_schemas.py:22-38`; audit run `--check` exited `0` | CI drift check wired (`.github/workflows/ci.yml:24-25`) |
| Run artifact validator script validates a real run dir or fails gracefully | **Pass** | `scripts/validate_run_artifacts.py:12-52`; audit run against `runs/20260223T015121Z_rag_baseline` exited `0` | Graceful not-found path implemented (`scripts/validate_run_artifacts.py:13-16`) |

## 4. P0/P1 Closure Table (Stage-1 -> Stage-2)

Stage-1 final report ended with **no confirmed P0/P1/P2/P3 issues remaining** (`POST_FLIGHT_REPORT.md:193-195`), so there were no open P0/P1 items to close in Stage-2.

| Stage-1 issue | Stage-2 status | Evidence | Notes |
|---|---|---|---|
| No open P0/P1 issues in Stage-1 final report | **Closed (N/A / none carried)** | `POST_FLIGHT_REPORT.md:195` | Stage-2 focused on next-step leverage items (live smoke, tests/CI depth, release hygiene, schemas), not defect closure |

## 5. What’s Now End-to-End Runnable (commands)

### Deterministic local ops (verified in this audit)

```bash
make help
make check
uv run --python 3.12 python -m unittest discover -s tests
uv run --python 3.12 python -m unittest tests.test_integration_edge_cases tests.test_script_smoke
./scripts/release_prep.sh --check
uv run --python 3.12 python scripts/sync_run_artifact_schemas.py --check
uv run --python 3.12 python scripts/validate_run_artifacts.py --run-dir runs/20260223T015121Z_rag_baseline
```

### Optional live-runtime confidence path (validated previously in Stage-2 execution)

```bash
LAB_LIVE_OLLAMA_SMOKE=1 ./scripts/live_ollama_smoke.sh
```

### Existing core lab workflows (still available; previously validated in Stage-1 audit/build run)

```bash
uv run lab doctor
uv run lab chat --prompt "hello"
uv run lab ingest --corpus data/corpus --index runs/index
uv run lab rag --index runs/index --question "What is RAG?"
uv run lab run --config experiments/rag_baseline.yaml
uv run lab report --run runs/<run_id>
uv run lab web --port 8000
```

## 6. Tests + CI Gates (what they actually validate)

### Test suite scope (current)

- Total test files: `10` (`tests/`)
- Categories now covered:
  - CLI parser behavior (`tests/test_cli_parser.py`)
  - RAG refusal threshold behavior (`tests/test_rag_threshold.py`)
  - fixture-based integration happy paths (`tests/test_integration_basics.py`)
  - web UI/API smoke behavior (`tests/test_web_smoke.py`)
  - integration edge/error paths (`tests/test_integration_edge_cases.py:30`)
  - script smoke checks (`tests/test_script_smoke.py:22`)
  - schema sync/model/validator checks (`tests/test_run_artifact_schemas.py:25`)
  - optional live Ollama smoke (env-gated, default skip) (`tests/test_live_ollama_smoke.py:38`)

### CI (default deterministic workflow)

`checks` job in `.github/workflows/ci.yml` validates:
- locked dependency sync (`.github/workflows/ci.yml:16-17`)
- lint (`.github/workflows/ci.yml:18-19`)
- shell syntax for helper scripts (`.github/workflows/ci.yml:20-21`)
- non-live script smoke tests (`.github/workflows/ci.yml:22-23`)
- run-artifact schema drift check (`.github/workflows/ci.yml:24-25`)
- full unittest suite (`.github/workflows/ci.yml:26-27`)
- optional Ludwig helper compatibility check (`.github/workflows/ci.yml:28-29`)

### Optional live-runtime workflow (separate)

`Live Ollama Smoke (Optional)` workflow (`.github/workflows/live-ollama-smoke.yml:1-23`):
- manual (`workflow_dispatch`) + scheduled
- self-hosted runner only
- `continue-on-error: true`
- runs gated live smoke wrapper (`scripts/live_ollama_smoke.sh`)

This separation is correct for stability and aligns with Stage-2 anti-overengineering/anti-flakiness goals.

## 7. Release/Packaging Readiness (baseline achieved?)

### Baseline status: **Yes (achieved)**

Stage-2 converts release readiness from documentation-only into executable checks:

- `scripts/release_prep.sh --check` enforces:
  - required file presence
  - version consistency (`pyproject.toml` vs `src/lab/__init__.py`)
  - clean git tree (strict mode)
  - `ruff` + full `unittest`
  - clear pass/fail summary (`scripts/release_prep.sh:60-129`)
- `Makefile` exposes `release-check` for operator convenience (`Makefile:63-66`)
- `RELEASE_CHECKLIST.md` now references release-prep and schema drift checks (`RELEASE_CHECKLIST.md:7-13`)
- schema drift is CI-checked (`.github/workflows/ci.yml:24-25`)

### What is still intentionally minimal

- No publish/tag automation, release bot, or package registry workflow (explicitly consistent with Stage-2 scope and local-first repo design)
- No front-facing proof asset generation (screenshots/GIFs/CI badge) in this stage

## 8. Remaining Issues (prioritized) + Minimal Fix Path

No confirmed **P0/P1** issues found in this Stage-2 audit run.

| Issue ID | Priority | Issue | Evidence | Minimal fix path |
|---|---|---|---|---|
| S2-R01 | P2 | Optional live smoke workflow depends on a pre-provisioned `self-hosted` runner but runner prerequisites/labels are not codified in workflow/docs | `.github/workflows/live-ollama-smoke.yml:10-23` | Add a short runner requirements section (labels, Ollama service state, model pre-pull expectations) to `PROMPT_EXECUTION_OPERATORS_GUIDE.md` or workflow comments |
| S2-R02 | P3 | `release_prep.sh` parses version values via ad hoc `python3` line scans, which is intentionally lightweight but somewhat brittle to formatting changes | `scripts/release_prep.sh:77-93` | Switch to a small `tomllib`-based parser (Python 3.11+) and a Python import for `lab.__version__`, or keep current approach and document formatting assumptions |
| S2-R03 | P3 | Run-artifact schemas are intentionally permissive (`extra=\"allow\"`) and cover a minimal stable subset only | `src/lab/run_artifact_models.py:9`, `:16`, `:24`, `:36` | Add versioned schema docs and gradually tighten fields used by reporting/web once contracts stabilize |
| S2-R04 | P3 | Optional live smoke is only in a separate workflow; default CI still cannot prove live-runtime behavior | `.github/workflows/live-ollama-smoke.yml:1-23`, `.github/workflows/ci.yml:1-29` | Keep default CI deterministic; optionally add a documented manual pre-release command transcript requirement in `RELEASE_CHECKLIST.md` (mostly already present) |
| S2-R05 | P3 | Front-facing proof assets (screenshots/GIFs/CI badge) remain absent, limiting external credibility even though engineering quality is high | `README.md`, `RELEASE_CHECKLIST.md:25-27` | Add proof assets and CI badge in a separate packaging/front-facing pass (explicitly out of scope for Stage-2) |

## 9. Anti-Overengineering Notes (what we avoided, what to prune)

### What Stage-2 avoided correctly

- **No new frameworks or services** were introduced (no Docker, queues, hosted DBs, browser-test stacks).
- **No CI flakiness regression**: live runtime checks are separated into an optional workflow (`.github/workflows/live-ollama-smoke.yml`) rather than being forced into default PR CI.
- **No schema explosion**: only run artifacts were modeled and generated, reusing existing `pydantic` instead of adding new schema libraries (`src/lab/run_artifact_models.py:5`, `scripts/sync_run_artifact_schemas.py:8`).
- **No orchestration sprawl**: `Makefile` remains a thin router over existing scripts/commands (`Makefile:8-66`).
- **No destructive cleanup footgun**: `clean-runs` is guarded by `CONFIRM=1` and path checks (`Makefile:46-61`).

### What to prune later (only if desired)

- If the repo stops using the optional live smoke workflow, remove `.github/workflows/live-ollama-smoke.yml` rather than expanding it into a more complex infrastructure path.
- If schema contracts stabilize, tighten `extra="allow"` and add versioning before adding more schema files.
- If `Makefile` grows much larger, split repeated shell logic into `scripts/` instead of turning it into a complex build system.

