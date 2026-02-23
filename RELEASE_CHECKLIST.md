# Release Checklist

Use this lightweight checklist before tagging or sharing a release of `local-llm-lab`.

## Pre-Release

- Confirm working tree status and review intended changes (`git status`, `git diff`)
- Run `ruff check .`
- Run `.venv/bin/python -m unittest discover -s tests`
- (Optional local runtime) Run `uv run lab doctor` and one CLI smoke command (`chat` or `rag`)
- (Optional local runtime) Run `LAB_LIVE_OLLAMA_SMOKE=1 ./scripts/live_ollama_smoke.sh` and capture success/skip output as evidence
- Review `README.md` and key docs for command/path drift
- Update `CHANGELOG.md` with a dated entry

## Packaging / Metadata

- Confirm `pyproject.toml` version is correct
- Confirm license status is correct (`LICENSE` + `pyproject.toml` metadata)
- Review dependency changes (`uv.lock`, `pyproject.toml`)

## Release Output

- Tag release (convention suggestion: `vX.Y.Z`)
- Capture proof artifacts for front-facing packaging (CLI screenshot, `/runs` UI screenshot, example summary)
- Note known limitations (local model variance, optional Ludwig compatibility, integration coverage boundaries)

## Post-Release

- Verify docs links and example commands from a fresh shell/session
- Record follow-up issues discovered during release verification
