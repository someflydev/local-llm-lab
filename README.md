# Local LLM Lab

A local, Ollama-based experimentation lab for chat, retrieval-augmented generation (RAG), evaluation, profiling, and optional web + Ludwig workflows on a Mac laptop.

## What this lab is

- A local-first repo for experimenting with LLM chat + RAG
- Built around Ollama, `uv`, `ruff`, and a single `lab` CLI
- Designed for iterative testing on constrained hardware (for example, M3 Pro with 18GB unified memory)

## Quickstart

```bash
./scripts/bootstrap_mac.sh
uv run lab doctor
uv run lab models recommend --task chat
uv run lab chat --prompt "hello"
```

## RAG Tutorial

Build the retrieval index:

```bash
uv run lab ingest --corpus data/corpus --index runs/index
```

Ask a retrieval-grounded question:

```bash
uv run lab rag --index runs/index --question "What command should an operator run first?"
```

You can also inspect raw retrieval output:

```bash
uv run lab retrieve --index runs/index --query "What is RAG?" --k 5
```

## Eval Tutorial

Run the baseline RAG evaluation harness:

```bash
uv run lab run --config experiments/rag_baseline.yaml
```

Then report the results:

```bash
uv run lab report --run runs/<run_id>
```

Compare multiple runs:

```bash
uv run lab compare --runs runs/<id1> runs/<id2>
```

## Profiling Tutorial

Run the local profiling harness:

```bash
uv run lab profile --model llama3 --n 5 --prompt-file data/prompts/profile_prompt.txt
```

This logs summaries to `runs/profile.jsonl`.

## Web UI (Optional)

Start the local FastAPI + Jinja2 UI:

```bash
uv run lab web --port 8000
```

Open:

- `http://127.0.0.1:8000`

## Ludwig Workflows (Optional)

Ludwig support is provided as an optional extra because it may pull heavy dependencies.

Install:

```bash
uv sync --extra ludwig
```

Run the small prompting workflow helper:

```bash
./scripts/run_ludwig_prompting.sh
```

See `docs/ludwig_workflows.md` for feasibility notes and templates.

## Troubleshooting Checklist

- Ollama not running:
  - Start it with `brew services start ollama` or `ollama serve`
- No models installed:
  - `ollama pull llama3`
- Embeddings model missing:
  - `ollama pull nomic-embed-text`
- Slow performance / swap pressure:
  - lower `num_ctx`
  - reduce `k`
  - choose a smaller/faster model
- Context too large:
  - reduce retrieval chunk size/overlap
  - reduce number of retrieved chunks
  - keep `num_ctx` at `4096` before trying `8192`

## Appendices

### Glossary (20+ terms)

Full glossary: `docs/glossary.md`

- LLM: Large Language Model, a model trained to predict and generate text.
- Neural Network: A layered function approximator that learns patterns from data.
- Transformer: A neural network architecture used by modern LLMs.
- Attention: A mechanism that lets the model focus on relevant tokens.
- Token: A chunk of text used as the model's basic processing unit.
- Context Window: The amount of tokenized text a model can consider at once.
- Inference: Running a trained model to generate outputs.
- Prompt: The input text sent to the model.
- System Prompt: High-priority instructions that constrain model behavior.
- Temperature: A sampling control that affects randomness/creativity.
- Hallucination: Confident but unsupported model output.
- RAG: Retrieval-Augmented Generation, combining retrieval with generation.
- Embedding: A numeric vector representation of text.
- Vector Store: A storage system for embeddings used in similarity search.
- Cosine Similarity: A similarity metric between vectors based on angle.
- Chunking: Splitting documents into smaller pieces for retrieval/indexing.
- Retrieval: Finding relevant document chunks for a query.
- Evaluation: Measuring behavior/performance against a dataset or rubric.
- Fine-tuning: Updating model parameters on task-specific data.
- In-context Learning: Teaching the model via examples in the prompt context.
- Quantization: Reducing numeric precision to lower memory/compute cost.
- Unified Memory: Shared memory architecture used by Apple Silicon CPU/GPU.
- Latency: Time to produce a response.
- Throughput: Work completed per unit time (for example chars/sec proxy).

### First 60 Minutes (Learning Path)

1. Run `uv run lab doctor` and confirm Ollama connectivity.
2. Run `uv run lab models status` and `uv run lab models recommend --task chat`.
3. Try `uv run lab chat --prompt "hello"`.
4. Build the index with `uv run lab ingest --corpus data/corpus --index runs/index`.
5. Test retrieval with `uv run lab retrieve --index runs/index --query "What is RAG?" --k 5`.
6. Test RAG with one answerable and one unanswerable question.
7. Run the baseline eval (`uv run lab run --config experiments/rag_baseline.yaml`) and inspect the report.
8. Run a short profile (`uv run lab profile --model llama3 --n 1 --prompt-file data/prompts/profile_prompt.txt`).
9. Optionally launch `uv run lab web --port 8000`.
10. Read `docs/rag_deep_dive.md` and `docs/neural_networks_101.md`.

## Verification Checklist

- doctor passes (or warns)
- chat works
- ingest works
- retrieve works
- rag works (including refusal)
- run/report works
- profile works
- web works (optional)

