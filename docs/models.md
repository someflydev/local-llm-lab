# Models Guide (M3 Pro 18GB, Ollama)

This guide explains the model policy used by `experiments/models.yaml` and the `lab models ...` commands.

## Why Llama 3 is the default

- It is the repo's known-good default for chat and RAG QA when installed.
- It is widely available in Ollama and behaves predictably for local experiments.
- The policy gives it the highest priority for `chat` and `rag_qa`.

## Why 8B-class models are the sweet spot on 18GB unified memory

- 8B-class models generally balance quality and responsiveness on a laptop.
- Larger models increase unified memory pressure and can trigger swap usage.
- For iterative lab work, faster feedback is usually more valuable than maximum model size.

## Why `num_ctx` defaults to 4096 (and when to try 8192)

- `4096` is a conservative default that reduces memory pressure and latency.
- `8192` is a cautious upper bound for this hardware profile, not a guaranteed safe default.
- Try `8192` only after confirming the machine stays responsive and swap pressure is manageable.

## Storage strategy with ~115GB free

- Pull the minimum set of models you need first (for example: `llama3`, `nomic-embed-text`).
- Avoid collecting many variants at once.
- Remove unused models regularly:
  - `ollama rm <model>`

## Task Defaults

| Task | Default model | Default settings | Why | When to change |
|---|---|---|---|---|
| `chat` | `llama3` (if installed) | `temperature=0.2`, `num_ctx=4096` | Stable known-good default on this hardware | Change if you need a faster/smaller variant or llama3 is not installed |
| `rag_qa` | `llama3` (if installed) | `temperature=0.2`, `num_ctx=4096`, conservative `k` | Good balance for grounded QA | Change for domain-specific experiments or memory constraints |
| `embeddings` | `nomic-embed-text` (if installed) | Default embedding call settings | Highest-priority policy embedding model | Change if unavailable or too slow/heavy |

## `lab models status`

`lab models status` compares installed Ollama models against the policy buckets:

- available known-good
- available preferred variants
- available embeddings
- available candidates
- missing recommended

This helps operators see what is installed versus what the repo recommends.

## `lab models recommend`

`lab models recommend --task <chat|rag_qa|embeddings>`:

- selects an installed model using the policy rules
- returns sensible defaults (`temperature`, `num_ctx`)
- suggests `ollama pull ...` commands when the preferred models are missing

Important:

- Candidate models like `deepseek-r1` and `kimi` are optional and may not exist locally.
- The repo should never assume those candidates are installed.

