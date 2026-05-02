import unittest
from typing import Any

from runtime_lab.llm_lab import continue_rag_adapter as adapter


class FakeResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class ContinueRagAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_post = adapter.requests.post

    def tearDown(self) -> None:
        adapter.requests.post = self.original_post

    def test_builds_prompt_when_endpoint_returns_evidence_found(self) -> None:
        def fake_post(url, headers, json, timeout):
            self.assertEqual(url, adapter.DEFAULT_ENDPOINT)
            self.assertEqual(headers, {"Content-Type": "application/json"})
            self.assertEqual(json, {"query": "que hace dry_run", "top_k": 3})
            self.assertEqual(timeout, adapter.DEFAULT_TIMEOUT_SECONDS)
            return FakeResponse(
                200,
                {
                    "status": adapter.EVIDENCE_FOUND,
                    "evidence": [
                        {
                            "text": "dry_run no ejecuta la tool real",
                            "source": "README.md",
                            "score": 1,
                        }
                    ],
                    "error": None,
                },
            )

        adapter.requests.post = fake_post

        result = adapter.build_continue_rag_prompt(" que hace dry_run ", top_k=3)

        self.assertEqual(result["status"], adapter.EVIDENCE_FOUND)
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["evidence"]), 1)
        self.assertIn("INSTRUCCIONES:", result["prompt"])
        self.assertIn("PREGUNTA:\nque hace dry_run", result["prompt"])
        self.assertIn("[1] source=README.md score=1.0", result["prompt"])
        self.assertIn("dry_run no ejecuta la tool real", result["prompt"])

    def test_returns_empty_prompt_when_endpoint_returns_evidence_not_found(self) -> None:
        def fake_post(url, headers, json, timeout):
            return FakeResponse(
                200,
                {
                    "status": adapter.EVIDENCE_NOT_FOUND,
                    "evidence": [],
                    "error": None,
                },
            )

        adapter.requests.post = fake_post

        result = adapter.build_continue_rag_prompt("pregunta sin evidencia")

        self.assertEqual(result["status"], adapter.EVIDENCE_NOT_FOUND)
        self.assertEqual(result["prompt"], "")
        self.assertEqual(result["evidence"], [])
        self.assertIsNone(result["error"])

    def test_returns_error_when_endpoint_times_out(self) -> None:
        def fake_post(url, headers, json, timeout):
            raise adapter.requests.exceptions.Timeout()

        adapter.requests.post = fake_post

        result = adapter.build_continue_rag_prompt("dry_run")

        self.assertEqual(result["status"], adapter.ERROR)
        self.assertEqual(result["prompt"], "")
        self.assertEqual(result["evidence"], [])
        self.assertEqual(result["error"], "RAG_ENDPOINT_TIMEOUT")

    def test_rejects_empty_query(self) -> None:
        def fail_if_called(url, headers, json, timeout):
            raise AssertionError("endpoint must not be called for invalid query")

        adapter.requests.post = fail_if_called

        result = adapter.build_continue_rag_prompt(" ")

        self.assertEqual(result["status"], adapter.ERROR)
        self.assertEqual(result["prompt"], "")
        self.assertEqual(result["evidence"], [])
        self.assertEqual(result["error"], "INVALID_QUERY")

    def test_rejects_top_k_out_of_range(self) -> None:
        def fail_if_called(url, headers, json, timeout):
            raise AssertionError("endpoint must not be called for invalid top_k")

        adapter.requests.post = fail_if_called

        too_low = adapter.build_continue_rag_prompt("dry_run", top_k=0)
        too_high = adapter.build_continue_rag_prompt("dry_run", top_k=11)

        self.assertEqual(too_low["status"], adapter.ERROR)
        self.assertEqual(too_low["error"], "INVALID_TOP_K")
        self.assertEqual(too_high["status"], adapter.ERROR)
        self.assertEqual(too_high["error"], "INVALID_TOP_K")


if __name__ == "__main__":
    unittest.main()
