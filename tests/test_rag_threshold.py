from __future__ import annotations

import unittest
from unittest.mock import patch

from lab.rag import RAG_REFUSAL, answer_question


class RagThresholdTests(unittest.TestCase):
    @patch("lab.rag.log_event")
    @patch("lab.rag._load_prompt_template")
    @patch("lab.rag.ChatOllama")
    @patch("lab.rag.retrieve")
    def test_threshold_is_opt_in_and_logs_telemetry(
        self,
        mock_retrieve,
        mock_chat_ollama,
        mock_load_prompt_template,
        mock_log_event,
    ) -> None:
        mock_retrieve.return_value = [
            {
                "path": "data/corpus/example.md",
                "chunk_id": "chunk-1",
                "score": 0.2,
                "full_text": "Example chunk text",
                "snippet": "Example",
            }
        ]
        mock_load_prompt_template.side_effect = ["sys", "q={question}\nctx={context}"]
        mock_chat_ollama.return_value.invoke.return_value = "A guessed answer"

        result = answer_question(
            question="Unanswerable?",
            index_dir="runs/index",
            chat_model_name="llama3",
            embed_model_name="nomic-embed-text",
            k=3,
            temperature=0.2,
            num_ctx=4096,
            refusal_score_threshold=0.35,
        )

        self.assertEqual(result["answer_text"], RAG_REFUSAL)
        self.assertEqual(result["citations"], [])
        _, payload = mock_log_event.call_args.args
        self.assertEqual(payload["refusal_score_threshold"], 0.35)
        self.assertTrue(payload["refusal_threshold_triggered"])
        self.assertEqual(payload["top_retrieval_score"], 0.2)


if __name__ == "__main__":
    unittest.main()
