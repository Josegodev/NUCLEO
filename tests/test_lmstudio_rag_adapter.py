import os
import unittest
from typing import Any

from runtime_lab.llm_lab import lmstudio_rag_adapter as adapter


class LMStudioRagAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_rag_search = adapter.rag_search
        self.original_get_models = adapter._get_lmstudio_model_ids
        self.original_call_chat = adapter._call_lmstudio_chat
        self.original_env = os.environ.copy()
        os.environ["LMSTUDIO_MODEL"] = "test-model"
        os.environ["LMSTUDIO_BASE_URL"] = "http://127.0.0.1:1234/v1"
        os.environ.pop("RAG_TOP_K", None)
        os.environ.pop("RAG_MAX_CONTEXT_CHARS", None)
        os.environ.pop("LMSTUDIO_TIMEOUT_SECONDS", None)
        os.environ.pop("LMSTUDIO_RAG_TRACE", None)

    def tearDown(self) -> None:
        adapter.rag_search = self.original_rag_search
        adapter._get_lmstudio_model_ids = self.original_get_models
        adapter._call_lmstudio_chat = self.original_call_chat
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_no_evidence_does_not_call_lmstudio(self) -> None:
        adapter.rag_search = self.fake_search([])
        adapter._get_lmstudio_model_ids = self.fail_if_get_models
        adapter._call_lmstudio_chat = self.fail_if_chat

        result = adapter.answer_with_lmstudio_rag("sin evidencia")

        self.assert_output_schema_stable(result)
        self.assertEqual(result["status"], adapter.NO_EVIDENCE)
        self.assertEqual(result["answer"], adapter.NO_EVIDENCE)
        self.assertEqual(result["evidence"], [])
        self.assertEqual(result["trace"]["fallback_reason"], adapter.NO_EVIDENCE)

    def test_lmstudio_unavailable_returns_fallback(self) -> None:
        adapter.rag_search = self.fake_search([self.evidence_result()])

        def unavailable(_base_url: str, _timeout_seconds: int) -> set[str]:
            raise adapter.LMStudioUnavailableError("server down")

        adapter._get_lmstudio_model_ids = unavailable
        adapter._call_lmstudio_chat = self.fail_if_chat

        result = adapter.answer_with_lmstudio_rag("con evidencia")

        self.assert_output_schema_stable(result)
        self.assertEqual(result["status"], adapter.LMSTUDIO_UNAVAILABLE)
        self.assertEqual(result["answer"], adapter.LMSTUDIO_UNAVAILABLE)
        self.assertEqual(
            result["trace"]["fallback_reason"],
            "models_endpoint_unavailable",
        )

    def test_model_not_loaded_returns_error(self) -> None:
        adapter.rag_search = self.fake_search([self.evidence_result()])
        adapter._get_lmstudio_model_ids = lambda _base_url, _timeout: {"other-model"}
        adapter._call_lmstudio_chat = self.fail_if_chat

        result = adapter.answer_with_lmstudio_rag("con evidencia")

        self.assert_output_schema_stable(result)
        self.assertEqual(result["status"], adapter.ERROR)
        self.assertIsNone(result["answer"])
        self.assertEqual(result["trace"]["fallback_reason"], "model_not_loaded")

    def test_ok_response_requires_valid_evidence_citation(self) -> None:
        adapter.rag_search = self.fake_search([self.evidence_result()])
        adapter._get_lmstudio_model_ids = self.loaded_models

        def cited_answer(**kwargs: Any) -> str:
            messages = kwargs["messages"]
            self.assertIn("[E1] path=docs/modules/planner.md score=0.9", messages[1]["content"])
            self.assertIn("Answer in Spanish.", messages[1]["content"])
            self.assertIn("Cite every factual claim", messages[1]["content"])
            return "El Planner prepara la siguiente accion propuesta [E1]."

        adapter._call_lmstudio_chat = cited_answer

        result = adapter.answer_with_lmstudio_rag("Que hace el Planner?", top_k=1)

        self.assert_output_schema_stable(result)
        self.assertEqual(result["status"], adapter.OK)
        self.assertEqual(
            result["answer"],
            "El Planner prepara la siguiente accion propuesta [E1].",
        )
        self.assertIsNone(result["trace"]["fallback_reason"])
        self.assertEqual(result["evidence"][0]["id"], "E1")

    def test_invalid_evidence_citation_returns_error(self) -> None:
        adapter.rag_search = self.fake_search([self.evidence_result()])
        adapter._get_lmstudio_model_ids = self.loaded_models
        adapter._call_lmstudio_chat = lambda **_kwargs: "Respuesta con cita falsa [E2]."

        result = adapter.answer_with_lmstudio_rag("Que hace el Planner?")

        self.assert_output_schema_stable(result)
        self.assertEqual(result["status"], adapter.ERROR)
        self.assertIsNone(result["answer"])
        self.assertEqual(
            result["trace"]["fallback_reason"],
            "invalid_evidence_citation",
        )

    def test_answer_without_citation_returns_answer_not_grounded(self) -> None:
        adapter.rag_search = self.fake_search([self.evidence_result()])
        adapter._get_lmstudio_model_ids = self.loaded_models
        adapter._call_lmstudio_chat = lambda **_kwargs: "Respuesta sin cita."

        result = adapter.answer_with_lmstudio_rag("Que hace el Planner?")

        self.assert_output_schema_stable(result)
        self.assertEqual(result["status"], adapter.ERROR)
        self.assertIsNone(result["answer"])
        self.assertEqual(
            result["trace"]["fallback_reason"],
            "answer_not_grounded",
        )

    def test_context_char_limit_applied(self) -> None:
        os.environ["RAG_MAX_CONTEXT_CHARS"] = "18"
        adapter.rag_search = self.fake_search(
            [
                {
                    "snippet": "uno dos tres cuatro cinco seis",
                    "file": "docs/context.md",
                    "doc_id": "context-1",
                    "score": 1.0,
                }
            ]
        )
        adapter._get_lmstudio_model_ids = self.loaded_models

        def cited_answer(**kwargs: Any) -> str:
            prompt = kwargs["messages"][1]["content"]
            self.assertIn("[E1] path=docs/context.md score=1.0", prompt)
            self.assertNotIn("cuatro cinco seis", prompt)
            return "Respuesta limitada [E1]."

        adapter._call_lmstudio_chat = cited_answer

        result = adapter.answer_with_lmstudio_rag("limite")

        self.assert_output_schema_stable(result)
        self.assertEqual(result["status"], adapter.OK)
        self.assertTrue(result["evidence"][0]["truncated"])
        self.assertLessEqual(len(result["evidence"][0]["text"]), 18)

    def test_output_schema_stable(self) -> None:
        adapter.rag_search = self.fake_search([self.evidence_result()])
        adapter._get_lmstudio_model_ids = self.loaded_models
        adapter._call_lmstudio_chat = lambda **_kwargs: "Respuesta valida [E1]."

        result = adapter.answer_with_lmstudio_rag("schema")

        self.assert_output_schema_stable(result)

    def fake_search(self, results: list[dict[str, Any]]):
        def _fake_search(question: str, top_k: int = 5) -> dict[str, Any]:
            return {
                "question": question,
                "status": "FOUND" if results else "NO_CONSTA_EN_DOCUMENTACION",
                "results": results,
            }

        return _fake_search

    def evidence_result(self) -> dict[str, Any]:
        return {
            "snippet": "El Planner prepara la siguiente accion propuesta.",
            "file": "docs/modules/planner.md",
            "doc_id": "planner-1",
            "score": 0.9,
            "line_start": 10,
            "line_end": 12,
        }

    def loaded_models(self, _base_url: str, _timeout_seconds: int) -> set[str]:
        return {"test-model"}

    def fail_if_get_models(self, *_args: Any, **_kwargs: Any) -> set[str]:
        raise AssertionError("LM Studio models endpoint must not be called")

    def fail_if_chat(self, **_kwargs: Any) -> str:
        raise AssertionError("LM Studio chat endpoint must not be called")

    def assert_output_schema_stable(self, result: dict[str, Any]) -> None:
        self.assertEqual(set(result), {"status", "answer", "evidence", "trace"})
        self.assertIn(
            result["status"],
            {
                adapter.OK,
                adapter.NO_EVIDENCE,
                adapter.LMSTUDIO_UNAVAILABLE,
                adapter.ERROR,
            },
        )
        self.assertTrue(result["answer"] is None or isinstance(result["answer"], str))
        self.assertIsInstance(result["evidence"], list)
        self.assertEqual(
            set(result["trace"]),
            {"query", "top_k", "model", "base_url", "fallback_reason"},
        )
        self.assertIsInstance(result["trace"]["query"], str)
        self.assertIsInstance(result["trace"]["top_k"], int)
        self.assertIsInstance(result["trace"]["model"], str)
        self.assertIsInstance(result["trace"]["base_url"], str)
        self.assertTrue(
            result["trace"]["fallback_reason"] is None
            or isinstance(result["trace"]["fallback_reason"], str)
        )


if __name__ == "__main__":
    unittest.main()
