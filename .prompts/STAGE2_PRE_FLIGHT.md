# Stage-2 Pre-Flight

## 1. Stage-2 Goal Alignment (mapped to report P0/P1)

### Factual alignment
- `POST_FLIGHT_REPORT.md` reports **94/100 completeness** and **9/10 excellence** (`POST_FLIGHT_REPORT.md:145`, `POST_FLIGHT_REPORT.md:168`).
- The report explicitly states **no confirmed P0/P1/P2/P3 issues remain** (`POST_FLIGHT_REPORT.md:195`), so Stage-2 should target leverage improvements and low-risk polish rather than defect remediation.
- `PROMPT_12.txt` directly targets the report’s **single most leverage improvement** (optional gated live-Ollama smoke validation).
- `PROMPT_13.txt`, `PROMPT_14.txt`, and `PROMPT_15.txt` map cleanly to the report’s top next steps (integration edge cases, shell/script health checks, contributor docs, release hygiene, lightweight automation hooks).
- `.prompts/PROMPT_STAGE2_MANIFEST.md` explicitly excludes frontend/product-site work, matching the user’s constraints.

### Alignment assessment
- **PASS**
- The Stage-2 set is goal-aligned, scope-controlled, and intentionally avoids front-facing/productization work.

## 2. Prompt Dependency Graph

### Planned order
1. `PROMPT_11.txt` — deterministic bring-up/check/teardown wiring
2. `PROMPT_12.txt` — optional gated live-Ollama smoke tests
3. `PROMPT_13.txt` — integration edge cases + script health + CI extensions
4. `PROMPT_14.txt` — contributor workflow + release hygiene automation
5. `PROMPT_15.txt` — lightweight run-artifact schemas + validation hooks

### Dependency graph (artifact-level)
- `PROMPT_11` creates `Makefile`
  - `PROMPT_14` may extend `Makefile` with `release-check` target (optional)
- `PROMPT_12` creates:
  - `tests/test_live_ollama_smoke.py`
  - `scripts/live_ollama_smoke.sh`
  - `.github/workflows/live-ollama-smoke.yml`
- `PROMPT_13` modifies `.github/workflows/ci.yml`
  - now explicitly required to preserve prior jobs/steps
- `PROMPT_14` creates `CONTRIBUTING.md`, `scripts/release_prep.sh`, and may touch `README.md`, `RELEASE_CHECKLIST.md`, `Makefile`
  - now explicitly required to preserve prior content/targets
- `PROMPT_15` adds schema/validation assets and modifies `.github/workflows/ci.yml`, `RELEASE_CHECKLIST.md`
  - now explicitly required to preserve prior jobs/checklist items

### Dependency hazard status
- **No blocking hidden dependency hazards found**
- Prior hazards were resolved:
  - destructive cleanup acceptance in `PROMPT_11` now uses a temp `RUNS_DIR` override
  - `PROMPT_14` now supports prompt-time verification via `--allow-dirty` (or equivalent)

## 3. Prompt-by-Prompt QA (issues + fixes)

### `PROMPT_11.txt`
- Status: **PASS**
- Strengths:
  - Clear exact artifact list and acceptance criteria
  - Cleanup targets explicitly support `RUNS_DIR` override
  - Destructive cleanup verification is constrained to a temp path
- Notes:
  - Cross-prompt preservation rule added for `README.md` / `RELEASE_CHECKLIST.md`

### `PROMPT_12.txt`
- Status: **PASS**
- Strengths:
  - Strong gating/skip semantics for live-runtime tests
  - Optional workflow is isolated from default CI
  - `--help` behavior is now explicit for the wrapper script
- Notes:
  - Shared docs are now protected by a preservation rule

### `PROMPT_13.txt`
- Status: **PASS**
- Strengths:
  - CI-safe checks (`bash -n`, deterministic unittest runs)
  - Script-health checks are now explicit and realistic (`run_ludwig_prompting.sh --check-only`, optional `live_ollama_smoke.sh --help`)
  - `.github/workflows/ci.yml` preservation rule reduces overwrite risk

### `PROMPT_14.txt`
- Status: **PASS**
- Strengths:
  - Release-prep script now has clear dual-mode expectation:
    - strict `--check`
    - prompt-safe `--check --allow-dirty` (or equivalent)
  - Acceptance criteria are now compatible with prompt execution before commit
  - Makefile/doc extension behavior is explicitly preservation-oriented

### `PROMPT_15.txt`
- Status: **PASS**
- Strengths:
  - Acceptance criteria are now deterministic (`--write` then `--check`)
  - Validation uses a fixture run directory under `tests/fixtures/`, not a historical local `runs/<id>` path
  - Historical `runs/<id>` validation is retained as optional extra evidence
  - `.github/workflows/ci.yml` preservation rule added

## 4. Acceptance Criteria Feasibility (CI-safe?)

### Summary
- **PASS (CI-safe with explicit gating where needed)**

### Feasibility table

| Prompt | Feasibility | CI-safe? | Notes |
|---|---|---|---|
| `PROMPT_11.txt` | Good | Yes | Cleanup verification now uses temp `RUNS_DIR`; no destructive requirement on real repo artifacts |
| `PROMPT_12.txt` | Good | Yes (default path) | Live smoke is gated/skippable and isolated in a separate optional workflow |
| `PROMPT_13.txt` | Good | Yes | Uses `bash -n` + deterministic `unittest`; no live runtime dependency |
| `PROMPT_14.txt` | Good | Yes (prompt-time) | `--allow-dirty` mode resolves the prompt-execution dirty-tree conflict |
| `PROMPT_15.txt` | Good | Yes | Deterministic fixture-based validation path removes dependence on local historical runs |

### Remaining feasibility cautions (non-blocking)
- `PROMPT_12` live smoke workflow may require self-hosted runners or pre-provisioned Ollama/model state; this is already acknowledged and properly gated.
- `PROMPT_15` schema sync should preserve stable JSON key ordering to avoid noisy diffs (already implied by guardrails, worth enforcing in implementation).

## 5. Naming / Path / Convention Alignment

### Findings
- Stage-2 prompt filenames are consistent and ordered (`PROMPT_11.txt`–`PROMPT_15.txt`).
- All planned artifacts follow existing repo conventions (`scripts/`, `tests/`, `.github/workflows/`, `schemas/`, repo-root docs).
- No front-facing web/product directories are introduced.
- No duplicate/conflicting naming plan detected (for example, no extra changelog/release docs beyond existing `CHANGELOG.md` / `RELEASE_CHECKLIST.md`).

### Convention alignment assessment
- **PASS**

### Minor note (non-blocking)
- `schemas/` is a new top-level directory. This is reasonable and consistent, but `CONTRIBUTING.md` (from `PROMPT_14`) should explicitly document it once introduced.

## 6. Overengineering Risks + Guardrails Verification

### Verification result
- **PASS**

### What the Stage-2 prompt set avoids (correctly)
- No new frameworks/test runners
- No new services or hosted dependencies
- No frontend/product-site scope
- No required live-runtime CI gate
- No broad refactors of `src/lab/web/app.py` / `src/lab/runner.py` beyond targeted improvements

### Guardrail quality
- `PROMPT_11`: Makefile kept as thin router; cleanup is opt-in and scoped
- `PROMPT_12`: live smoke is gated and optional
- `PROMPT_13`: high-signal tests only; no framework churn
- `PROMPT_14`: lightweight release/contributor automation only
- `PROMPT_15`: schema scope explicitly limited to run artifacts and generated from `pydantic`

## 7. Recommended Edits (patch list) + Priority

### Required before execution
- **None**

### Optional polish (can defer)
1. **P3** `.prompts/PROMPT_STAGE2_MANIFEST.md`
   - Clarify the DoD line for release-prep validation by mentioning strict `--check` is a final/release-mode check and prompt-time verification may use `--allow-dirty`.
   - Impact: documentation clarity only.

2. **P3** `.prompts/PROMPT_STAGE2_MANIFEST.md`
   - Add one line noting that `PROMPT_15` uses a fixture run directory for deterministic validator acceptance.
   - Impact: manifest clarity only; prompt text is already correct.

## 8. Go/No-Go Decision

### Decision: **GO**

Reason:
- The blocking pre-flight issues identified in the first pass were addressed in the Stage-2 prompt files.
- Acceptance criteria are now realistic, sequence-safe, and CI-safe (with explicit gating where live runtime is involved).
- Shared-file edit hazards are mitigated with explicit preservation rules.
- Stage-2 remains tightly scoped to backend/ops/test/release quality and excludes front-facing scope.

