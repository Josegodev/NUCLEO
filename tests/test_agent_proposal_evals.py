import json
import tempfile
import unittest
from pathlib import Path

from app.tools.local.echo_tool import EchoTool
from runtime_lab.llm_lab.evals.run_agent_proposal_evals import (
    DEFAULT_CASES_PATH,
    evaluate_case,
    load_eval_cases,
    run_suite,
    summarize_case_results,
)


def proposal_output(action, arguments: dict) -> str:
    return json.dumps(
        {
            "intent": "eval proposal",
            "suggested_action": action,
            "arguments": arguments,
            "confidence": 0.9,
        }
    )


class StaticRouter:
    def __init__(self, output: str, fallback_reason: str | None = None) -> None:
        self.output = output
        self.fallback_reason = fallback_reason
        self.calls = 0

    def generate(self, prompt: str, backend, model_id: str | None) -> dict:
        self.calls += 1
        return {
            "output": self.output,
            "model_used": model_id or "missing",
            "backend_used": getattr(backend, "value", backend),
            "latency_ms": 3.0,
            "fallback_used": False,
            "fallback_reason": self.fallback_reason,
        }


class UnavailableRouter:
    def generate(self, prompt: str, backend, model_id: str | None) -> dict:
        return {
            "output": "",
            "model_used": model_id or "missing",
            "backend_used": getattr(backend, "value", backend),
            "latency_ms": 1.0,
            "fallback_used": False,
            "fallback_reason": "OPENAI_API_KEY is not configured.",
        }


class PromptAwareRouter:
    def generate(self, prompt: str, backend, model_id: str | None) -> dict:
        if "haz echo de hola" in prompt:
            output = proposal_output("echo", {"text": "hola"})
        elif "dame informacion del sistema" in prompt:
            output = proposal_output("system_info", {})
        else:
            output = proposal_output(None, {})

        return {
            "output": output,
            "model_used": model_id or "missing",
            "backend_used": getattr(backend, "value", backend),
            "latency_ms": 2.0,
            "fallback_used": False,
            "fallback_reason": None,
        }


class AgentProposalEvalTests(unittest.TestCase):
    def test_load_eval_cases_json(self) -> None:
        payload = load_eval_cases(DEFAULT_CASES_PATH)

        self.assertEqual(payload["version"], "agent_proposal_eval.v1")
        self.assertEqual(payload["cases"][0]["id"], "echo_basic_es")
        self.assertEqual(payload["cases"][0]["expected"]["arguments"], {"text": "hola"})

    def test_calculates_score(self) -> None:
        metrics = summarize_case_results(
            [
                {
                    "case_id": "ok",
                    "valid_json": True,
                    "valid_contract": True,
                    "expected_action_match": True,
                    "expected_arguments_match": True,
                    "fallback_used": False,
                    "provider_unavailable": False,
                    "critical_failure": False,
                    "latency_ms": 10.0,
                },
                {
                    "case_id": "bad_args",
                    "valid_json": True,
                    "valid_contract": False,
                    "expected_action_match": True,
                    "expected_arguments_match": False,
                    "fallback_used": True,
                    "provider_unavailable": False,
                    "critical_failure": False,
                    "latency_ms": 20.0,
                },
            ]
        )

        self.assertEqual(metrics["valid_json_rate"], 1.0)
        self.assertEqual(metrics["valid_contract_rate"], 0.5)
        self.assertEqual(metrics["fallback_rate"], 0.5)
        self.assertEqual(metrics["avg_latency_ms"], 15.0)
        self.assertEqual(metrics["score"], 0.75)
        self.assertFalse(metrics["runtime_candidate"])

    def test_provider_unavailable_does_not_break_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact = run_suite(
                models=["gpt-4o-mini"],
                backends=["openai"],
                output_dir=Path(tmpdir),
                model_router=UnavailableRouter(),
                timestamp="20260501_000000",
            )

        result = artifact["results"][0]
        self.assertTrue(result["provider_unavailable"])
        self.assertFalse(result["runtime_candidate"])
        self.assertEqual(result["critical_failures"], [])
        self.assertIn("ranking", artifact)

    def test_echo_requires_text_not_message(self) -> None:
        payload = load_eval_cases(DEFAULT_CASES_PATH)
        echo_case = payload["cases"][0]

        result = evaluate_case(
            case=echo_case,
            model="test-model",
            backend="local",
            model_router=StaticRouter(proposal_output("echo", {"message": "hola"})),
        )

        self.assertTrue(result["valid_json"])
        self.assertFalse(result["valid_contract"])
        self.assertTrue(result["expected_action_match"])
        self.assertFalse(result["expected_arguments_match"])
        self.assertTrue(result["fallback_used"])
        self.assertIn("message", result["fallback_reason"])

    def test_eval_does_not_execute_tool_run(self) -> None:
        original_run = EchoTool.run

        def fail_if_called(self, payload, context=None):
            raise AssertionError("eval suite must not call tool.run")

        EchoTool.run = fail_if_called
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                artifact = run_suite(
                    models=["test-model"],
                    backends=["local"],
                    output_dir=Path(tmpdir),
                    model_router=PromptAwareRouter(),
                    timestamp="20260501_000001",
                )
        finally:
            EchoTool.run = original_run

        result = artifact["results"][0]
        self.assertEqual(result["valid_contract_rate"], 1.0)
        self.assertEqual(result["fallback_rate"], 0.0)
        self.assertTrue(result["runtime_candidate"])


if __name__ == "__main__":
    unittest.main()
