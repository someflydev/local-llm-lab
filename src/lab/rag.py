from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from langchain_ollama import ChatOllama

from lab.logging_jsonl import log_event
from lab.retrieval import retrieve

RAG_REFUSAL = "I don't know from the provided documents."


def _load_prompt_template(name: str) -> str:
    path = Path("src") / "lab" / "prompts" / name
    return path.read_text(encoding="utf-8")


def _build_context(retrieved: list[dict[str, Any]]) -> str:
    if not retrieved:
        return "(no retrieved context)"
    parts: list[str] = []
    for item in retrieved:
        parts.append(
            "\n".join(
                [
                    "---",
                    f"path: {item['path']}",
                    f"chunk_id: {item['chunk_id']}",
                    "text:",
                    item["full_text"],
                ]
            )
        )
    return "\n".join(parts)


def _response_text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return " ".join(str(part) for part in content).strip()
    return str(content).strip()


def answer_question(
    question: str,
    index_dir: str,
    chat_model_name: str,
    embed_model_name: str,
    k: int,
    temperature: float,
    num_ctx: int,
    question_id: str | None = None,
) -> dict[str, Any]:
    start = time.perf_counter()
    retrieved = retrieve(query=question, k=k, index_dir=index_dir, embed_model_name=embed_model_name)
    citations = [{"path": item["path"], "chunk_id": item["chunk_id"]} for item in retrieved]

    if not retrieved:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        payload = {
            "question_id": question_id,
            "model": chat_model_name,
            "embed_model": embed_model_name,
            "k": k,
            "num_ctx": num_ctx,
            "latency_ms": latency_ms,
            "citations": [],
            "answer_preview": RAG_REFUSAL[:160],
        }
        log_event("rag", payload)
        return {
            "answer_text": RAG_REFUSAL,
            "citations": [],
            "retrieved": retrieved,
            "latency_ms": latency_ms,
        }

    system_prompt = _load_prompt_template("rag_system.txt")
    user_prompt = _load_prompt_template("rag_user.txt").format(
        question=question.strip(),
        context=_build_context(retrieved),
    )

    llm = ChatOllama(
        model=chat_model_name,
        temperature=temperature,
        num_ctx=num_ctx,
    )
    response = llm.invoke(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )
    answer_text = _response_text(response)

    # Conservative refusal normalization: low-similarity top hit often indicates unsupported queries.
    top_score = retrieved[0]["score"] if retrieved else 0.0
    if top_score < 0.35 and answer_text != RAG_REFUSAL:
        answer_text = RAG_REFUSAL

    if answer_text == RAG_REFUSAL:
        citations = []
    else:
        # Ensure citations are present in the answer body even if the model omits them.
        sources_block = "\n".join([f"- {c['path']} (chunk_id={c['chunk_id']})" for c in citations])
        if sources_block and "chunk_id" not in answer_text:
            answer_text = f"{answer_text}\n\nCitations:\n{sources_block}"

    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    payload = {
        "question_id": question_id,
        "model": chat_model_name,
        "embed_model": embed_model_name,
        "k": k,
        "num_ctx": num_ctx,
        "latency_ms": latency_ms,
        "citations": citations,
        "answer_preview": answer_text[:160],
    }
    log_event("rag", payload)
    return {
        "answer_text": answer_text,
        "citations": citations,
        "retrieved": retrieved,
        "latency_ms": latency_ms,
    }

