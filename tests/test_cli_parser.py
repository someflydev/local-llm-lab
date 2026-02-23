from __future__ import annotations

import unittest

from lab.cli import build_parser


class CliParserTests(unittest.TestCase):
    def test_rag_parser_accepts_optional_refusal_threshold(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "rag",
                "--question",
                "What is RAG?",
                "--refusal-score-threshold",
                "0.4",
            ]
        )
        self.assertEqual(args.command, "rag")
        self.assertEqual(args.question, "What is RAG?")
        self.assertAlmostEqual(args.refusal_score_threshold, 0.4)

    def test_doctor_parser_keeps_base_url_default(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["doctor"])
        self.assertEqual(args.base_url, "http://127.0.0.1:11434")


if __name__ == "__main__":
    unittest.main()
