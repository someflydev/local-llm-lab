# Neural Networks 101 (Conceptual, Non-Mathy)

## What a neural network is

A neural network is a program that learns patterns from examples.

Instead of writing explicit rules for every situation, you train it on data and it adjusts internal weights so it can make useful predictions on new inputs.

## Why neural networks matter for LLMs

Large language models (LLMs) are neural networks trained on large amounts of text.

They learn statistical patterns about:

- words and phrases
- structure and grammar
- common associations
- likely next tokens in a sequence

## A simple mental model

Think of a neural network as a layered signal-processing system:

- input goes in (tokens)
- each layer transforms the representation
- later layers build higher-level patterns
- the model predicts the next token repeatedly

That repeated next-token prediction is what produces generated text.

## What “learning” means here

During training:

- the model makes predictions
- those predictions are compared to the correct next tokens
- the model's weights are adjusted to reduce error over many examples

After training, inference uses those learned weights without changing them (unless you fine-tune).

## Where transformers fit in

Most modern LLMs are based on the **transformer** architecture.

The key idea is **attention**, which helps the model decide which earlier tokens matter most when predicting the next token.

This is a big reason transformers work well on language tasks.

## Important limitations

Neural networks are powerful but not magical.

- They can hallucinate.
- They can be wrong confidently.
- They depend heavily on prompts and context.
- They do not automatically know what is true in your local documents.

That is why this repo uses RAG, refusal behavior, and evaluation.

## Why local experimentation helps learning

Running models locally helps you see how practical settings affect behavior:

- context size
- model size
- retrieval quality
- latency and responsiveness

This makes the concepts more concrete than reading theory alone.

## Next steps

- Run `lab chat` and compare outputs with different temperatures.
- Build the retrieval index with `lab ingest`.
- Ask answerable and unanswerable RAG questions with `lab rag`.
- Run the baseline evaluation harness and inspect the report.

