# Performance Profiling Notes

This lab uses lightweight profiling to compare practical latency/throughput behavior locally.

## What the profiler measures

- Wall time per run
- Average wall time across repeated runs
- Character-per-second proxy (based on generated text length)

## Unified memory and swap pressure

On Apple Silicon laptops, model memory usage competes with the rest of the system in unified memory.

When memory pressure is high:

- the system may become less responsive
- latency can spike
- swap usage can increase dramatically

## Quantization (high-level)

Quantization reduces memory usage and can improve practical local inference viability.

- Smaller quantized models are often better for iterative experiments
- The quality/speed tradeoff depends on task and model family

## Context window tradeoffs

Larger context windows can help some tasks, but they also increase:

- memory pressure
- latency
- risk of degraded responsiveness

Use `4096` first, then test `8192` carefully if the machine remains stable.

## Practical knobs to tune

- lower `num_ctx`
- choose a smaller model
- reduce retrieved chunks (`k`)
- reduce chunk size in retrieval pipelines

## Profiling command

```bash
uv run lab profile --model llama3 --n 5 --prompt-file data/prompts/profile_prompt.txt
```

Example output format (fields):

- model
- prompt_file
- n
- num_ctx
- temperature
- average_wall_ms
- average_chars_per_sec
- runs[] with per-run wall_ms / chars_per_sec

