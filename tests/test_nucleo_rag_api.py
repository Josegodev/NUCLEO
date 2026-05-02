import asyncio
import json
import unittest
from typing import Any

from runtime_lab.llm_lab import nucleo_rag_api as api


def asgi_request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    return asyncio.run(_asgi_request(method, path, payload))


async def _asgi_request(
    method: str,
    path: str,
    payload: dict[str, Any] | None,
) -> tuple[int, dict[str, Any]]:
    body = b"" if payload is None else json.dumps(payload).encode("utf-8")
    response: dict[str, Any] = {
        "status": 0,
        "body": b"",
    }
    request_sent = False

    async def receive() -> dict[str, Any]:
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        if message["type"] == "http.response.start":
            response["status"] = message["status"]
        elif message["type"] == "http.response.body":
            response["body"] += message.get("body", b"")

    headers = [
        (b"host", b"testserver"),
    ]
    if payload is not None:
        headers.extend(
            [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ]
        )

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "root_path": "",
    }

    await api.app(scope, receive, send)
    decoded = response["body"].decode("utf-8")
    return int(response["status"]), json.loads(decoded)


class NucleoRagApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_rag_search = api.rag_search

    def tearDown(self) -> None:
        api.rag_search = self.original_rag_search

    def test_health_returns_ok(self) -> None:
        status_code, payload = asgi_request("GET", "/health")

        self.assertEqual(status_code, 200)
        self.assertEqual(payload, {"status": "ok", "service": "nucleo_rag_api"})

    def test_empty_query_is_rejected(self) -> None:
        status_code, payload = asgi_request(
            "POST",
            "/nucleo-rag/query",
            {"query": " ", "top_k": 3},
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(payload["status"], api.RagStatus.ERROR.value)
        self.assertEqual(payload["evidence"], [])
        self.assertIsInstance(payload["error"], str)

    def test_top_k_out_of_range_is_rejected(self) -> None:
        status_code, payload = asgi_request(
            "POST",
            "/nucleo-rag/query",
            {"query": "dry_run", "top_k": 11},
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(payload["status"], api.RagStatus.ERROR.value)
        self.assertEqual(payload["evidence"], [])
        self.assertIsInstance(payload["error"], str)

    def test_query_response_uses_closed_status_and_evidence_list(self) -> None:
        def fake_search(question: str, top_k: int = 5) -> dict[str, Any]:
            self.assertEqual(question, "dry_run")
            self.assertEqual(top_k, 3)
            return {
                "question": question,
                "status": "FOUND",
                "results": [
                    {
                        "snippet": "dry_run evidence",
                        "file": str(api.REPO_ROOT / "README.md"),
                        "score": "0.5",
                    }
                ],
            }

        api.rag_search = fake_search

        status_code, payload = asgi_request(
            "POST",
            "/nucleo-rag/query",
            {"query": "dry_run", "top_k": 3},
        )

        allowed_statuses = {status.value for status in api.RagStatus}
        self.assertEqual(status_code, 200)
        self.assertIn(payload["status"], allowed_statuses)
        self.assertIsInstance(payload["evidence"], list)
        self.assertIsNone(payload["error"])
        self.assertEqual(
            payload["evidence"],
            [{"text": "dry_run evidence", "source": "README.md", "score": 0.5}],
        )

    def test_continue_context_returns_context_items_from_evidence(self) -> None:
        def fake_search(question: str, top_k: int = 5) -> dict[str, Any]:
            self.assertEqual(question, "dry_run")
            self.assertEqual(top_k, 2)
            return {
                "question": question,
                "status": "FOUND",
                "results": [
                    {
                        "snippet": "dry_run evidence",
                        "file": str(api.REPO_ROOT / "README.md"),
                        "score": 0.5,
                    }
                ],
            }

        api.rag_search = fake_search

        with self.assertLogs(api.logger, level="INFO") as logs:
            status_code, payload = asgi_request(
                "POST",
                "/nucleo-rag/context",
                {
                    "query": " dry_run ",
                    "fullInput": "@nucleo-rag dry_run",
                    "options": {"top_k": 2},
                },
            )

        self.assertEqual(status_code, 200)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["name"], "nucleo-rag:1:README.md")
        self.assertIn("README.md", payload[0]["description"])
        self.assertIn("source: README.md", payload[0]["content"])
        self.assertIn("dry_run evidence", payload[0]["content"])
        self.assertIn("result_count=1", logs.output[0])
        self.assertIn("fallback_reason=None", logs.output[0])

    def test_continue_context_returns_empty_list_when_no_evidence(self) -> None:
        def fake_search(question: str, top_k: int = 5) -> dict[str, Any]:
            self.assertEqual(question, "pregunta sin evidencia")
            return {
                "question": question,
                "status": "NO_CONSTA_EN_DOCUMENTACION",
                "results": [],
            }

        api.rag_search = fake_search

        with self.assertLogs(api.logger, level="INFO") as logs:
            status_code, payload = asgi_request(
                "POST",
                "/nucleo-rag/context",
                {"query": "pregunta sin evidencia"},
            )

        self.assertEqual(status_code, 200)
        self.assertEqual(payload, [])
        self.assertIn("result_count=0", logs.output[0])
        self.assertIn("fallback_reason=NO_EVIDENCE", logs.output[0])

    def test_continue_context_falls_back_to_full_input_query(self) -> None:
        def fake_search(question: str, top_k: int = 5) -> dict[str, Any]:
            self.assertEqual(question, "@nucleo-rag dry_run")
            self.assertEqual(top_k, api.DEFAULT_CONTEXT_TOP_K)
            return {
                "question": question,
                "status": "FOUND",
                "results": [
                    {
                        "snippet": "fallback query evidence",
                        "file": "runtime_lab/llm_lab/README.md",
                        "score": 1,
                    }
                ],
            }

        api.rag_search = fake_search

        status_code, payload = asgi_request(
            "POST",
            "/nucleo-rag/context",
            {"query": " ", "fullInput": "@nucleo-rag dry_run"},
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(len(payload), 1)
        self.assertIn("fallback query evidence", payload[0]["content"])

    def test_continue_context_rejects_invalid_options_as_empty_context(self) -> None:
        def fail_if_called(question: str, top_k: int = 5) -> dict[str, Any]:
            raise AssertionError("RAG must not be called for invalid options")

        api.rag_search = fail_if_called

        with self.assertLogs(api.logger, level="INFO") as logs:
            status_code, payload = asgi_request(
                "POST",
                "/nucleo-rag/context",
                {"query": "dry_run", "options": ["top_k", 2]},
            )

        self.assertEqual(status_code, 200)
        self.assertEqual(payload, [])
        self.assertIn("result_count=0", logs.output[0])
        self.assertIn("fallback_reason=INVALID_OPTIONS", logs.output[0])


if __name__ == "__main__":
    unittest.main()
