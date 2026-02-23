# Prompt Templates and Refusal Behavior

A good RAG prompt should instruct the model to answer only from retrieved context. If the evidence is missing, the model should refuse clearly instead of guessing.

This lab uses a strict refusal string for unsupported questions so evaluation can score refusal correctness deterministically.

