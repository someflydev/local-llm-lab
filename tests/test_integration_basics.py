from __future__ import annotations

import contextlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import orjson

from lab.ingest import ingest_corpus
from lab.retrieval import retrieve
from lab.runner import RAG_REFUSAL, run_config


@contextlib.contextmanager
def _cwd(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


class _FakeIngestEmbeddings:
    def __init__(self, model: str) -> None:
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_vector_for_text(text) for text in texts]


class _FakeRetrieveEmbeddings:
    def __init__(self, model: str) -> None:
        self.model = model

    def embed_query(self, query: str) -> list[float]:
        return _vector_for_text(query)


def _vector_for_text(text: str) -> list[float]:
    lowered = text.lower()
    return [
        1.0 if "rag" in lowered else 0.0,
        1.0 if "ollama" in lowered else 0.0,
    ]


class IntegrationBasicsTests(unittest.TestCase):
    @patch("lab.retrieval.OllamaEmbeddings", _FakeRetrieveEmbeddings)
    @patch("lab.ingest.OllamaEmbeddings", _FakeIngestEmbeddings)
    def test_ingest_and_retrieve_fixture_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus_dir = root / "corpus"
            corpus_dir.mkdir()
            (corpus_dir / "rag.md").write_text("RAG combines retrieval and generation.", encoding="utf-8")
            (corpus_dir / "ops.md").write_text("Ollama runs local models.", encoding="utf-8")
            index_dir = root / "index"

            with _cwd(root):
                metadata = ingest_corpus(
                    corpus_dir=corpus_dir,
                    index_dir=index_dir,
                    embed_model_name="fake-embed",
                    chunk_size_chars=500,
                    overlap_chars=10,
                )
                self.assertEqual(metadata["embedding_model"], "fake-embed")
                self.assertEqual(metadata["file_count"], 2)
                self.assertTrue((index_dir / "index.sqlite").exists())

                results = retrieve(
                    query="What is RAG?",
                    k=2,
                    index_dir=index_dir,
                    embed_model_name="fake-embed",
                )

            self.assertEqual(len(results), 2)
            self.assertIn("rag", results[0]["path"].lower())
            self.assertGreaterEqual(results[0]["score"], results[1]["score"])

    @patch("lab.runner._resolve_chat_models", return_value=["fake-chat"])
    @patch("lab.runner._resolve_embed_model", return_value="fake-embed")
    @patch("lab.runner.ingest_corpus")
    @patch("lab.runner.answer_question")
    def test_runner_writes_summary_and_results_schema(
        self,
        mock_answer_question,
        mock_ingest_corpus,
        _mock_resolve_embed,
        _mock_resolve_chat,
    ) -> None:
        def fake_answer_question(**kwargs):
            question = kwargs["question"]
            if "capital of france" in question.lower():
                return {
                    "answer_text": RAG_REFUSAL,
                    "citations": [],
                    "retrieved": [],
                    "latency_ms": 12.5,
                }
            return {
                "answer_text": "RAG combines retrieval and generation.",
                "citations": [{"path": "corpus/rag.md", "chunk_id": 0}],
                "retrieved": [{"path": "corpus/rag.md", "chunk_id": 0, "score": 0.9}],
                "latency_ms": 23.4,
            }

        mock_answer_question.side_effect = fake_answer_question
        mock_ingest_corpus.side_effect = lambda **kwargs: Path(kwargs["index_dir"]).mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "data" / "corpus").mkdir(parents=True)
            (root / "data" / "corpus" / "rag.md").write_text(
                "RAG combines retrieval and generation.",
                encoding="utf-8",
            )
            dataset_path = root / "data" / "eval.jsonl"
            rows = [
                {
                    "id": "q1",
                    "question": "What is RAG?",
                    "answerable": True,
                    "expected_keywords": ["retrieval", "generation"],
                },
                {
                    "id": "q2",
                    "question": "What is the capital of France?",
                    "answerable": False,
                    "expected_keywords": [],
                },
            ]
            dataset_path.write_bytes(b"\n".join(orjson.dumps(r) for r in rows) + b"\n")
            config_path = root / "experiments" / "test_eval.yaml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join(
                    [
                        "name: test_eval",
                        "task: rag_eval",
                        "corpus_dir: data/corpus",
                        "chat_models:",
                        "  - fake-chat",
                        "embed_model: fake-embed",
                        "k: 2",
                        "num_ctx: 1024",
                        "temperature: 0.2",
                        "chunk_size_chars: 500",
                        "overlap_chars: 10",
                        "dataset_path: data/eval.jsonl",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with _cwd(root):
                run_dir = run_config(config_path)
                self.assertTrue((run_dir / "summary.json").exists())
                self.assertTrue((run_dir / "results.jsonl").exists())
                summary = orjson.loads((run_dir / "summary.json").read_bytes())
                self.assertEqual(summary["config_name"], "test_eval")
                self.assertEqual(summary["question_count"], 2)
                self.assertIn("overall", summary["aggregate_scores"])
                lines = (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(lines), 2)
                first = orjson.loads(lines[0])
                self.assertIn("question_id", first)
                self.assertIn("citations", first)
                self.assertIn("retrieved", first)

            self.assertEqual(mock_answer_question.call_count, 2)


if __name__ == "__main__":
    unittest.main()
