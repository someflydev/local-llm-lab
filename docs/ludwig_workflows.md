# Ludwig Workflows (Local, M3 Pro 18GB)

This repo includes Ludwig workflow artifacts in a way that is honest about local laptop limits.

## What is feasible on 18GB unified memory

- Prompting workflows: practical
- In-context learning (ICL): practical for tiny datasets and short runs
- Fine-tuning: treat as a template unless you confirm the exact model + config fits your machine

Keep runs small:

- Use tiny datasets first (dozens to low hundreds of rows)
- Prefer short outputs
- Run one workflow at a time
- Watch swap pressure and responsiveness

## Prompting vs ICL vs Fine-tuning

- Prompting: direct instruction execution with no parameter updates
- ICL: provide examples in the prompt/context without changing model weights
- Fine-tuning: update model parameters (usually heaviest and least laptop-friendly)

## Installation (isolated Ludwig environment)

Keep Ludwig in a separate virtual environment so the main lab lockfile stays stable.
Default helper/CI target: Ludwig `0.10.4` on Python 3.12.

```bash
uv venv .venv-ludwig --python 3.12
printf 'numpy<2\n' > /tmp/ludwig-runtime-constraints.txt
printf 'Cython<3\n' > /tmp/ludwig-build-constraints.txt
uv pip install --python .venv-ludwig/bin/python \
  --constraints /tmp/ludwig-runtime-constraints.txt \
  --build-constraints /tmp/ludwig-build-constraints.txt \
  "ludwig==0.10.4"
```

The runtime constraint avoids NumPy 2.x ABI mismatches with older Ludwig-transitive binary wheels (for example `pyarrow`).
The build constraint avoids a Python 3.12 source-build failure for `pyyaml==6.0`
in Ludwig's dependency set by forcing a PyYAML-compatible Cython version (`Cython<3`).

Legacy note: if you intentionally use `ludwig==0.7.5`, prefer Python 3.11 because it may resolve `scikit-learn==1.1.3`, which is not Python 3.12-friendly.

You can override the helper's defaults via environment variables, for example:
`LUDWIG_EXPECTED_VERSION=0.10.4 LUDWIG_PYTHON_VERSION=3.12 ./scripts/run_ludwig_prompting.sh --check-only`

## Artifacts in this repo

- Dataset: `data/ludwig/prompting.jsonl`
- Runnable prompting config: `ludwig/prompting.yaml`
- ICL config template: `ludwig/icl.yaml`
- Tiny fine-tune template: `ludwig/tiny_finetune.yaml`
- Helper script: `scripts/run_ludwig_prompting.sh`

## Run the prompting workflow

```bash
./scripts/run_ludwig_prompting.sh
```

The script checks whether Ludwig is installed in `.venv-ludwig`. If not, it prints the exact `uv` commands to create that isolated environment and exits with a warning instead of failing hard.
It also checks the detected Ludwig version and validates that `ludwig experiment --help` includes `--config` before running the workflow command.
You can run only the validation checks (without executing the workflow) using:

```bash
./scripts/run_ludwig_prompting.sh --check-only
```

## Compatibility notes

- Default helper target: `ludwig==0.10.4` (CI best-effort check)
- Legacy fallback: `ludwig==0.7.5` on Python 3.11
- If you install a different Ludwig version, run `./scripts/run_ludwig_prompting.sh` and read the version/syntax validation output before assuming the command shape is compatible.
