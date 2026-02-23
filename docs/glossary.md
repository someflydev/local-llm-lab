# Glossary

## Core terms

- **LLM**: Large Language Model used for text generation and reasoning-like tasks.
- **Neural Network**: A trainable function made of layers that transforms inputs into outputs.
- **Transformer**: The dominant neural network architecture behind modern LLMs.
- **Attention**: The mechanism that helps a transformer focus on relevant tokens.
- **Token**: A subword/word-like unit processed by the model.
- **Context Window**: Maximum tokens a model can consider in one request.
- **Inference**: Running a trained model to generate output.
- **Prompt**: Input instructions/content provided to the model.
- **System Prompt**: High-priority behavior constraints for the model.
- **Temperature**: Sampling setting that changes output randomness.

## Reliability and RAG

- **Hallucination**: Unsupported or fabricated model output.
- **RAG (Retrieval-Augmented Generation)**: Retrieval plus generation using local documents.
- **Embedding**: Vector representation of text for similarity search.
- **Vector Store**: Storage/index of embeddings for retrieval.
- **Cosine Similarity**: Vector similarity metric used in retrieval ranking.
- **Chunking**: Splitting documents into smaller retrieval units.
- **Retrieval**: Selecting relevant chunks for a query.
- **Citation**: Reference to the supporting source chunk used in an answer.
- **Refusal**: Intentionally declining to answer when evidence is insufficient.

## Experimentation and ops

- **Evaluation**: Measuring model/system behavior with a dataset and scoring rules.
- **Fine-tuning**: Training a model further on task-specific data.
- **In-context Learning (ICL)**: Providing examples in the prompt instead of changing weights.
- **Quantization**: Lowering precision to reduce memory usage and often improve speed.
- **Unified Memory**: Shared memory pool on Apple Silicon used by CPU/GPU workloads.
- **Latency**: Time required to produce a response.
- **Throughput**: Rate of work over time (e.g., chars/sec proxy).
- **num_ctx**: Ollama context setting controlling token window size.
- **Ollama**: Local model runtime used by this repo.
- **JSONL**: Newline-delimited JSON format used for logs and datasets.

