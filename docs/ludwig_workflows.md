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
This helper path is currently documented/tested against Ludwig `0.7.5`.

```bash
uv venv .venv-ludwig --python 3.12
uv pip install --python .venv-ludwig/bin/python "ludwig==0.7.5"
```

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

## Compatibility notes

- Tested helper target: `ludwig==0.7.5`
- If you install a different Ludwig version, run `./scripts/run_ludwig_prompting.sh` and read the version/syntax validation output before assuming the command shape is compatible.
