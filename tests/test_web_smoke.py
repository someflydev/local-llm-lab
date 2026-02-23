from __future__ import annotations

import contextlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import orjson
from fastapi.testclient import TestClient

from lab.web.app import app


@contextlib.contextmanager
def _cwd(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


class WebSmokeTests(unittest.TestCase):
    def test_runs_pages_smoke_and_preview_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_dir = root / "runs" / "20260223T000000Z_test"
            run_dir.mkdir(parents=True)
            summary = {
                "run_id": "20260223T000000Z_test",
                "config_name": "test",
                "models": ["fake-chat"],
                "aggregate_scores": {"overall": {"accuracy_proxy": 1.0}},
                "latency_stats": {"overall": {"avg_ms": 10.0}},
            }
            (run_dir / "summary.json").write_bytes(orjson.dumps(summary))
            with (run_dir / "results.jsonl").open("wb") as fh:
                for i in range(105):
                    fh.write(
                        orjson.dumps(
                            {
                                "question_id": f"q{i}",
                                "model": "fake-chat",
                                "score": 1,
                                "latency_ms": 10.0,
                                "answer_text": f"answer {i}",
                            }
                        )
                    )
                    fh.write(b"\n")

            with _cwd(root):
                client = TestClient(app)
                resp_runs = client.get("/runs")
                self.assertEqual(resp_runs.status_code, 200)
                self.assertIn("20260223T000000Z_test", resp_runs.text)

                resp_detail = client.get("/runs/20260223T000000Z_test")
                self.assertEqual(resp_detail.status_code, 200)
                self.assertIn("Preview limited to first 100 rows", resp_detail.text)

    @patch("lab.web.app.answer_question")
    @patch("lab.web.app.OllamaClient")
    @patch("lab.web.app._recommended_model")
    def test_chat_and_rag_post_smoke(
        self,
        mock_recommended_model,
        mock_ollama_client,
        mock_answer_question,
    ) -> None:
        def fake_recommend(task: str) -> str:
            if task == "embeddings":
                return "fake-embed"
            return "fake-chat"

        mock_recommended_model.side_effect = fake_recommend
        mock_ollama_client.return_value.chat_generate.return_value = {
            "text": "hello",
            "latency_ms": 12.3,
            "raw_response_snippet": "{}",
        }
        mock_answer_question.return_value = {
            "answer_text": "RAG answer",
            "citations": [{"path": "data/corpus/rag.md", "chunk_id": 0}],
            "retrieved": [{"path": "data/corpus/rag.md", "chunk_id": 0, "score": 0.9, "snippet": "RAG"}],
            "latency_ms": 34.5,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with _cwd(Path(tmpdir)):
                client = TestClient(app)

                resp_chat = client.post(
                    "/chat",
                    data={"prompt": "hello", "temperature": "0.2", "num_ctx": "1024"},
                )
                self.assertEqual(resp_chat.status_code, 200)
                self.assertIn("Response", resp_chat.text)
                self.assertIn("hello", resp_chat.text)

                resp_rag = client.post(
                    "/rag",
                    data={
                        "question": "What is RAG?",
                        "index_dir": "runs/index",
                        "temperature": "0.2",
                        "num_ctx": "1024",
                        "k": "3",
                    },
                )
                self.assertEqual(resp_rag.status_code, 200)
                self.assertIn("RAG answer", resp_rag.text)
                self.assertIn("data/corpus/rag.md", resp_rag.text)


if __name__ == "__main__":
    unittest.main()
