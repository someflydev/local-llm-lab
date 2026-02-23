from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class CitationItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    path: str
    chunk_id: int


class RetrievedItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    path: str
    chunk_id: int
    score: float


class RunResultRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    question_id: str
    model: str
    score: int | float
    latency_ms: float
    answer_text: str
    citations: list[CitationItem] = []
    retrieved: list[RetrievedItem] = []


class RunSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    run_id: str
    config_name: str
    models: list[str]
    aggregate_scores: dict[str, Any]
    latency_stats: dict[str, Any]
    question_count: int | None = None


def run_summary_schema() -> dict[str, Any]:
    return RunSummary.model_json_schema()


def run_result_row_schema() -> dict[str, Any]:
    return RunResultRow.model_json_schema()

