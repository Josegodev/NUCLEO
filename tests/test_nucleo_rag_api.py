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


if __name__ == "__main__":
    unittest.main()
