from __future__ import annotations

import contextlib
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import orjson
from fastapi.testclient import TestClient

from lab.ingest import ingest_corpus
from lab.retrieval import retrieve
from lab.runner import _call_rag_with_controls, run_config
from lab.web.app import JOB_STORE, app


@contextlib.contextmanager
def _cwd(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


class IntegrationEdgeCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        JOB_STORE.clear()

    def test_ingest_rejects_missing_or_empty_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            missing = root / "missing"
            empty = root / "empty"
            empty.mkdir()
            with self.assertRaises(FileNotFoundError):
                ingest_corpus(missing, root / "index", "fake-embed")
            with self.assertRaises(ValueError):
                ingest_corpus(empty, root / "index", "fake-embed")

    def test_retrieve_validates_inputs_and_missing_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaises(ValueError):
                retrieve(query="", k=1, index_dir=root / "index", embed_model_name="fake-embed")
            with self.assertRaises(ValueError):
                retrieve(query="x", k=0, index_dir=root / "index", embed_model_name="fake-embed")
            with self.assertRaises(ValueError):
                retrieve(query="x", k=1, index_dir=root / "index", embed_model_name=None)
            with self.assertRaises(FileNotFoundError):
                retrieve(query="x", k=1, index_dir=root / "index", embed_model_name="fake-embed")

    @patch("lab.runner.answer_question", side_effect=RuntimeError("boom"))
    def test_rag_call_controls_retries_and_returns_error_result(self, _mock_answer_question) -> None:
        result, attempts = _call_rag_with_controls(
            question="What is RAG?",
            index_dir="runs/index",
            chat_model_name="fake-chat",
            embed_model_name="fake-embed",
            k=2,
            temperature=0.2,
            num_ctx=1024,
            question_id="q1",
            refusal_score_threshold=None,
            per_call_timeout_s=None,
            max_retries=1,
            retry_backoff_s=0.0,
        )
        self.assertEqual(attempts, 2)
        self.assertIn("[rag_error]", result["answer_text"])
        self.assertEqual(result["error"], "boom")

    def test_rag_call_controls_timeout_returns_error_result(self) -> None:
        def slow_answer(**_: object) -> dict[str, object]:
            time.sleep(0.02)
            return {
                "answer_text": "late",
                "citations": [],
                "retrieved": [],
                "latency_ms": 20.0,
            }

        with patch("lab.runner.answer_question", side_effect=slow_answer):
            result, attempts = _call_rag_with_controls(
                question="What is RAG?",
                index_dir="runs/index",
                chat_model_name="fake-chat",
                embed_model_name="fake-embed",
                k=2,
                temperature=0.2,
                num_ctx=1024,
                question_id="q1",
                refusal_score_threshold=None,
                per_call_timeout_s=0.001,
                max_retries=0,
                retry_backoff_s=0.0,
            )
        self.assertEqual(attempts, 1)
        self.assertIn("timed out", str(result["error"]).lower())
        self.assertEqual(result["latency_ms"], 0.0)

    @patch("lab.runner._resolve_chat_models", return_value=["fake-chat"])
    @patch("lab.runner._resolve_embed_model", return_value="fake-embed")
    @patch("lab.runner.ingest_corpus")
    @patch("lab.runner.answer_question")
    def test_runner_writes_error_records_and_summary_counts(
        self,
        mock_answer_question,
        mock_ingest_corpus,
        _mock_embed,
        _mock_chat,
    ) -> None:
        mock_ingest_corpus.side_effect = lambda **kwargs: Path(kwargs["index_dir"]).mkdir(parents=True, exist_ok=True)
        mock_answer_question.side_effect = [
            {
                "answer_text": "RAG combines retrieval and generation.",
                "citations": [{"path": "corpus/rag.md", "chunk_id": 0}],
                "retrieved": [{"path": "corpus/rag.md", "chunk_id": 0, "score": 0.9}],
                "latency_ms": 12.0,
            },
            RuntimeError("synthetic failure"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "data" / "corpus").mkdir(parents=True)
            (root / "data" / "corpus" / "rag.md").write_text("RAG basics", encoding="utf-8")
            dataset_path = root / "data" / "eval.jsonl"
            dataset_rows = [
                {"id": "q1", "question": "What is RAG?", "answerable": True, "expected_keywords": ["rag"]},
                {"id": "q2", "question": "Unknown?", "answerable": False, "expected_keywords": []},
            ]
            dataset_path.write_bytes(b"\n".join(orjson.dumps(r) for r in dataset_rows) + b"\n")
            config_path = root / "experiments" / "edge_eval.yaml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join(
                    [
                        "name: edge_eval",
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
                summary = orjson.loads((run_dir / "summary.json").read_bytes())
                self.assertEqual(summary["question_count"], 2)
                self.assertEqual(summary["error_count"], 1)
                self.assertEqual(summary["timeout_count"], 0)
                rows = [orjson.loads(line) for line in (run_dir / "results.jsonl").read_bytes().splitlines()]
                self.assertEqual(len(rows), 2)
                self.assertIsNone(rows[0]["error"])
                self.assertEqual(rows[1]["error"], "synthetic failure")
                self.assertIn("[rag_error]", rows[1]["answer_text"])

    @patch("lab.runner._resolve_chat_models", return_value=["fake-chat"])
    @patch("lab.runner._resolve_embed_model", return_value="fake-embed")
    @patch("lab.runner.ingest_corpus")
    @patch("lab.runner.answer_question")
    def test_runner_raises_on_malformed_dataset_row_missing_keys(
        self,
        _mock_answer_question,
        mock_ingest_corpus,
        _mock_embed,
        _mock_chat,
    ) -> None:
        mock_ingest_corpus.side_effect = lambda **kwargs: Path(kwargs["index_dir"]).mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "data" / "corpus").mkdir(parents=True)
            (root / "data" / "corpus" / "rag.md").write_text("RAG basics", encoding="utf-8")
            (root / "data" / "bad.jsonl").write_bytes(
                orjson.dumps({"question": "Missing id", "answerable": True, "expected_keywords": []}) + b"\n"
            )
            config_path = root / "experiments" / "bad.yaml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join(
                    [
                        "name: bad_eval",
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
                        "dataset_path: data/bad.jsonl",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with _cwd(root):
                with self.assertRaises(KeyError):
                    run_config(config_path)

    def test_web_unknown_job_and_run_detail_clamps_pagination(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_dir = root / "runs" / "20260223T000000Z_edge"
            run_dir.mkdir(parents=True)
            summary = {
                "run_id": "20260223T000000Z_edge",
                "config_name": "edge",
                "models": ["fake-chat"],
                "aggregate_scores": {"overall": {"accuracy_proxy": 1.0}},
                "latency_stats": {"overall": {"avg_ms": 10.0}},
            }
            (run_dir / "summary.json").write_bytes(orjson.dumps(summary))
            with (run_dir / "results.jsonl").open("wb") as fh:
                fh.write(
                    orjson.dumps(
                        {
                            "question_id": "q1",
                            "model": "fake-chat",
                            "score": 1,
                            "latency_ms": 10.0,
                            "answer_text": "ok",
                        }
                    )
                )
                fh.write(b"\n")

            with _cwd(root):
                client = TestClient(app)
                missing_job = client.get("/api/jobs/no-such-job")
                self.assertEqual(missing_job.status_code, 200)
                self.assertEqual(missing_job.json()["error"], "job not found")

                missing_run = client.get("/runs/not-real")
                self.assertEqual(missing_run.status_code, 404)
                self.assertIn("Run not found", missing_run.text)

                clamped = client.get("/runs/20260223T000000Z_edge?offset=-5&limit=9999")
                self.assertEqual(clamped.status_code, 200)
                self.assertIn("Offset: 0 | Limit: 500", clamped.text)


if __name__ == "__main__":
    unittest.main()
