# RAG Deep Dive (Beginner-Friendly)

## What RAG is

RAG stands for **Retrieval-Augmented Generation**.

Instead of asking a model to answer from memory alone, a RAG system:

1. retrieves relevant documents (or chunks),
2. passes that evidence to the model,
3. asks the model to answer using only the retrieved context.

This improves transparency and usually reduces hallucination risk.

## Why this repo uses RAG

This repo is a local experimentation lab. RAG is useful here because it lets you:

- test document ingestion and retrieval quality
- compare prompts and models on grounded tasks
- inspect citations and refusal behavior
- run repeatable evaluations locally

## How this repo implements RAG

### 1) Corpus

- Source documents live in `data/corpus/`
- They are small markdown files describing the lab and RAG concepts

### 2) Chunking

- `src/lab/text_chunking.py` performs deterministic character-based chunking
- Default chunking parameters:
  - `chunk_size_chars=900`
  - `overlap_chars=120`

### 3) Embeddings + ingestion

- `src/lab/ingest.py` reads the corpus
- it creates embeddings using `langchain-ollama` (`OllamaEmbeddings`)
- it stores chunks + embeddings in sqlite at `runs/index/index.sqlite` (or per-run index directories)

### 4) Retrieval

- `src/lab/retrieval.py` embeds the user query
- it loads stored embeddings
- it computes cosine similarity in Python
- it returns top-k results with scores and snippets

### 5) RAG prompting

- Templates live in `src/lab/prompts/rag_system.txt` and `src/lab/prompts/rag_user.txt`
- `src/lab/rag.py` builds a context block from retrieved chunks and calls `ChatOllama`
- The prompt requires:
  - context-only answers
  - citations (`path` + `chunk_id`)
  - exact refusal string when unsupported

### 6) Evaluation

- `data/rag_eval_questions.jsonl` includes answerable and unanswerable questions
- `src/lab/runner.py` scores:
  - keyword matching for answerable questions
  - exact refusal correctness for unanswerable questions

## Why refusals matter

A RAG system that answers everything is not reliable. Unanswerable questions are important because they test whether the system can avoid guessing.

This repo uses a strict refusal string to make evaluation deterministic:

`I don't know from the provided documents.`

## Practical tuning tips

- Start with smaller `k` (for example `3` to `5`)
- Keep `num_ctx` conservative (`4096`)
- Keep chunks short enough to avoid bloated prompts
- Compare runs after changing one variable at a time

