import json
import unittest

from app.adapters.model_router import ModelBackendCall, ModelRouter
from app.policies.models import (
    PolicyDecision,
    PolicyDecisionValue,
    PolicyValidatedField,
)
from app.runtime.orchestrator import AgentRuntime
from app.runtime.planner import Planner
from app.runtime.planner_augmentation import LLMAssistedPlannerStrategy
from app.runtime.tracing import InMemoryTracer
from app.schemas.context import ExecutionContext
from app.schemas.requests import AgentBackend, AgentRequest
from app.schemas.responses import ExecutionStatus
from app.tools.local.echo_tool import EchoTool


class SpyEchoTool(EchoTool):
    def __init__(self) -> None:
        self.calls = 0

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        self.calls += 1
        return super().run(payload, context=context)


class SpyRegistry:
    def __init__(self, tool) -> None:
        self._tool = tool
        self.get_calls = 0

    def get(self, tool_name: str):
        self.get_calls += 1
        if tool_name == self._tool.name:
            return self._tool
        return None


class CountingPolicyEngine:
    def __init__(self) -> None:
        self.calls = 0

    def evaluate(
        self,
        tool_name: str,
        payload: dict,
        dry_run: bool,
        context: ExecutionContext,
    ) -> PolicyDecision:
        self.calls += 1
        return PolicyDecision(
            decision=PolicyDecisionValue.ALLOW,
            reason="allowed by test",
            validated_fields=[PolicyValidatedField.TOOL_NAME],
        )


def context() -> ExecutionContext:
    return ExecutionContext(
        user_id="u1",
        username="tester",
        roles=["admin"],
        authenticated=True,
        request_id="agent-console-test",
    )


def tracer() -> InMemoryTracer:
    return InMemoryTracer(timestamp_provider=lambda: "2026-05-01T00:00:00+00:00")


def valid_echo_output() -> str:
    return json.dumps(
        {
            "intent": "echo requested",
            "suggested_action": "echo",
            "arguments": {"text": "hola"},
            "confidence": 0.9,
        }
    )


def console_request(dry_run: bool = True) -> AgentRequest:
    return AgentRequest.model_validate(
        {
            "input": "say hola",
            "context": {},
            "options": {
                "backend": "auto",
                "model_id": "llama3.1:8b",
                "agent_mode": "proposal_only",
                "dry_run": dry_run,
            },
        }
    )


class AgentConsoleTests(unittest.TestCase):
    def test_console_contract_maps_input_options_and_forces_dry_run(self) -> None:
        request = console_request(dry_run=False)

        self.assertEqual(request.user_input, "say hola")
        self.assertEqual(request.options.backend, AgentBackend.AUTO)
        self.assertTrue(request.dry_run)
        self.assertTrue(request.options.dry_run)

    def test_proposal_only_does_not_execute_tool_and_invokes_policy(self) -> None:
        tool = SpyEchoTool()
        registry = SpyRegistry(tool)
        policy_engine = CountingPolicyEngine()
        runtime = AgentRuntime(
            runtime_planner=Planner(
                strategy=LLMAssistedPlannerStrategy(
                    enabled=True,
                    proposal_provider=lambda llm_input, request: valid_echo_output(),
                )
            ),
            runtime_policy_engine=policy_engine,
            tool_registry=registry,
            runtime_tracer=tracer(),
        )

        response = runtime.run(console_request(dry_run=False), context())

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertEqual(policy_engine.calls, 1)
        self.assertEqual(registry.get_calls, 1)
        self.assertEqual(tool.calls, 0)
        self.assertFalse(response.result["executed"])
        self.assertEqual(response.result["proposal"]["suggested_action"], "echo")

    def test_dry_run_true_prevents_tool_execution(self) -> None:
        tool = SpyEchoTool()
        runtime = AgentRuntime(
            runtime_planner=Planner(
                strategy=LLMAssistedPlannerStrategy(
                    enabled=True,
                    proposal_provider=lambda llm_input, request: valid_echo_output(),
                )
            ),
            runtime_policy_engine=CountingPolicyEngine(),
            tool_registry=SpyRegistry(tool),
            runtime_tracer=tracer(),
        )

        response = runtime.run(console_request(dry_run=True), context())

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertEqual(response.result["dry_run"], True)
        self.assertEqual(response.result["executed"], False)
        self.assertEqual(tool.calls, 0)

    def test_backend_auto_fallback_works(self) -> None:
        def failing_local(model_id: str, prompt: str) -> ModelBackendCall:
            return ModelBackendCall(
                backend_used=AgentBackend.LOCAL,
                model_used=model_id,
                success=False,
                output=None,
                latency_ms=1.0,
                error_type="model_not_available",
                error_message="local unavailable",
            )

        def successful_openai(model_id: str, prompt: str) -> ModelBackendCall:
            return ModelBackendCall(
                backend_used=AgentBackend.OPENAI,
                model_used=model_id,
                success=True,
                output=valid_echo_output(),
                latency_ms=2.0,
            )

        result = ModelRouter(
            local_caller=failing_local,
            openai_caller=successful_openai,
        ).generate(
            prompt="proposal prompt",
            backend=AgentBackend.AUTO,
            model_id="llama3.1:8b",
        )

        self.assertEqual(result["backend_used"], "openai")
        self.assertEqual(result["model_used"], "gpt-4o-mini")
        self.assertTrue(result["fallback_used"])
        self.assertIn("local unavailable", result["fallback_reason"])

    def test_invalid_llm_output_uses_deterministic_fallback(self) -> None:
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            proposal_provider=lambda llm_input, request: "not-json",
        )

        plan = Planner(strategy=strategy).create_plan(
            AgentRequest.model_validate(
                {
                    "input": "system info",
                    "options": {
                        "backend": "auto",
                        "model_id": "llama3.1:8b",
                        "agent_mode": "proposal_only",
                        "dry_run": True,
                    },
                }
            )
        )

        self.assertEqual(plan.source, "rule:system_info")
        self.assertTrue(plan.metadata["fallback_used"])
        self.assertEqual(plan.metadata["proposal"]["suggested_action"], "system_info")

    def test_tool_registry_does_not_execute_tool(self) -> None:
        tool = SpyEchoTool()
        registry = SpyRegistry(tool)
        runtime = AgentRuntime(
            runtime_planner=Planner(
                strategy=LLMAssistedPlannerStrategy(
                    enabled=True,
                    proposal_provider=lambda llm_input, request: valid_echo_output(),
                )
            ),
            runtime_policy_engine=CountingPolicyEngine(),
            tool_registry=registry,
            runtime_tracer=tracer(),
        )

        runtime.run(console_request(), context())

        self.assertGreater(registry.get_calls, 0)
        self.assertEqual(tool.calls, 0)


if __name__ == "__main__":
    unittest.main()
