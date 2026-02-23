# Stage-2 Prompt Manifest

## Stage-2 Goals
Maximize engineering completeness/excellence from the current post-flight baseline (already ~`94/100`, `9/10`) without expanding product scope or adding frontend work. Stage-2 focuses on:
- optional live-runtime confidence (gated live-Ollama smoke tests)
- deterministic local bring-up/check/teardown wiring
- stronger non-live regression coverage (edge cases + shell/script health)
- contributor/release hygiene
- lightweight run-artifact schemas that unlock automation and compatibility checks

## Explicit Exclusions (Stage-2 Anti-Scope)
- No frontend/product website work
- No major architectural refactors
- No new external services (databases, queues, hosted APIs)
- No heavy dependencies unless clearly justified by an acceptance criterion
- No mandatory live-model CI gate in the default workflow

## Definition of Done for Stage-2 (DoD-S2)
- [ ] `Makefile` provides `help`, `check`, `verify`, `smoke-fixture`, `clean-runs-preview`, `clean-runs`
  - Evidence: `Makefile` exists and `make help` lists the targets
- [ ] Deterministic local checks run without live Ollama
  - Command: `make check` exits `0`
- [ ] Optional live-Ollama smoke tests exist and are gated/skippable
  - Evidence: `tests/test_live_ollama_smoke.py`, `scripts/live_ollama_smoke.sh`, `.github/workflows/live-ollama-smoke.yml`
  - Command: `uv run --python 3.12 python -m unittest discover -s tests` still exits `0` without live runtime
- [ ] Default CI includes shell/script health checks and remains deterministic
  - Evidence: `.github/workflows/ci.yml` has shell syntax/smoke step(s), no required live-Ollama job
- [ ] Additional edge-case integration tests cover failure paths (ingest/retrieve/runner/web/script wrappers)
  - Command: `uv run --python 3.12 python -m unittest tests.test_integration_edge_cases tests.test_script_smoke`
- [ ] Contributor workflow is documented
  - Evidence: `CONTRIBUTING.md` includes setup, testing, prompt changes, and repo layout guidance
- [ ] Release prep script validates repo readiness without mutating files
  - Command: `./scripts/release_prep.sh --check`
- [ ] Run artifact schema models + checked-in schemas exist and are sync-checkable
  - Command: `uv run --python 3.12 python scripts/sync_run_artifact_schemas.py --check`
- [ ] Run artifact validator script can validate a real run dir or fail gracefully with clear guidance
  - Command: `uv run --python 3.12 python scripts/validate_run_artifacts.py --run-dir <path>`

## Planned Prompt Sequence (Recommended Order)
1. `PROMPT_11.txt` — Capstone Deterministic Bring-Up / Check / Teardown Wiring
   - First because it establishes repeatable local commands used by later prompts.
2. `PROMPT_12.txt` — Optional Gated Live-Ollama Smoke Tests (Most-Leverage Improvement)
   - Targets the report’s biggest remaining confidence gap without changing default CI.
3. `PROMPT_13.txt` — Integration Edge Cases + Script Health Checks + CI Extensions
   - Expands deterministic coverage and CI safety rails while keeping complexity low.
4. `PROMPT_14.txt` — Contributor Workflow + Release Hygiene Automation
   - Codifies how to work in the repo and adds a release-prep baseline.
5. `PROMPT_15.txt` — Lightweight Run-Artifact Schemas + Validation Hooks
   - Adds compatibility checks and automation hooks after core workflows and tests are stabilized.

## Prompt-to-Report Target Mapping
- Report “single most leverage improvement” (live-Ollama automation): `PROMPT_12`
- Top Next Step #1 (optional gated live-Ollama smoke tests): `PROMPT_12`
- Top Next Step #4 (expand integration tests): `PROMPT_13`
- Top Next Step #8 (shellcheck/shell smoke tests): `PROMPT_13`
- Top Next Step #10 (`CONTRIBUTING.md`): `PROMPT_14`
- Complexity risk control (avoid overbuilding orchestration): `PROMPT_11`, `PROMPT_13`, `PROMPT_15` guardrails

## Stop Condition (Mandatory)
If any prompt fails one or more of its acceptance criteria:
1. Stop the sequence immediately.
2. Report:
   - the failing command/check
   - exact error output
   - files changed in that prompt
   - minimal recovery options (retry / revert last prompt / patch-forward)
3. Do not start the next Stage-2 prompt until the failure is resolved or explicitly deferred.

## Execution Notes
- Each prompt must be runnable independently on the current audited repo.
- Prefer minimal patches over refactors.
- Preserve existing behavior unless the prompt explicitly changes it.
- Keep live-runtime automation optional and clearly gated.

