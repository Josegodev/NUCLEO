import json
import tempfile
import unittest

from app.policies.models import (
    PolicyDecision,
    PolicyDecisionValue,
    PolicyValidatedField,
)
from app.runtime.augmentation_service import (
    AugmentationService,
    serialize_tool_catalog,
)
from app.runtime.orchestrator import AgentRuntime
from app.runtime.planner import Planner
from app.runtime.tracing import InMemoryTracer
from app.schemas.context import ExecutionContext
from app.schemas.requests import AgentRequest, AgentRunOptions
from app.schemas.responses import ExecutionStatus
from app.services.approval.approval_store import ApprovalStore
from app.tools.local.echo_tool import EchoTool
from app.tools.registry import registry as production_registry


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


class SpyEchoTool(EchoTool):
    def __init__(self) -> None:
        self.calls = 0

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        self.calls += 1
        return super().run(payload, context=context)


class EchoOnlyRegistry:
    def __init__(self, tool: EchoTool) -> None:
        self._tool = tool

    def get(self, tool_name: str):
        if tool_name == self._tool.name:
            return self._tool
        return None

    def list_contracts(self):
        return [self._tool.contract]


def context() -> ExecutionContext:
    return ExecutionContext(
        user_id="u1",
        username="tester",
        roles=["admin"],
        authenticated=True,
        request_id="augmentation-service-test",
    )


def request(user_input: str = "say hola") -> AgentRequest:
    return AgentRequest(
        user_input=user_input,
        options=AgentRunOptions(),
    )


def provider_output(payload: dict) -> str:
    return json.dumps(payload)


class AugmentationServiceTests(unittest.TestCase):
    def test_invalid_json_uses_fallback(self) -> None:
        service = AugmentationService(
            proposal_provider=lambda llm_input, agent_request: "not-json"
        )

        result = service.run(
            request=request("system info"),
            context=context(),
            tool_catalog=serialize_tool_catalog(production_registry),
        )

        self.assertTrue(result.fallback_used)
        self.assertIsNone(result.proposed_action)
        self.assertIn("Invalid JSON", result.fallback_reason)

    def test_unknown_tool_uses_fallback(self) -> None:
        service = AugmentationService(
            proposal_provider=lambda llm_input, agent_request: provider_output(
                {
                    "intent": "unknown tool",
                    "suggested_action": "missing_tool",
                    "arguments": {},
                    "confidence": 0.7,
                }
            )
        )

        result = service.run(
            request=request("system info"),
            context=context(),
            tool_catalog=serialize_tool_catalog(production_registry),
        )

        self.assertTrue(result.fallback_used)
        self.assertIsNone(result.proposed_action)
        self.assertIn("outside serialized catalog", result.fallback_reason)

    def test_invalid_payload_uses_fallback(self) -> None:
        service = AugmentationService(
            proposal_provider=lambda llm_input, agent_request: provider_output(
                {
                    "intent": "echo requested",
                    "suggested_action": "echo",
                    "arguments": {"message": "hola"},
                    "confidence": 0.9,
                }
            )
        )

        result = service.run(
            request=request("say hola"),
            context=context(),
            tool_catalog=serialize_tool_catalog(production_registry),
        )

        self.assertTrue(result.fallback_used)
        self.assertIsNone(result.proposed_action)
        self.assertIn("payload", result.fallback_reason)

    def test_no_llm_for_non_proposal_request_uses_normal_planner_flow(self) -> None:
        tool = SpyEchoTool()
        policy_engine = CountingPolicyEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = AgentRuntime(
                runtime_planner=Planner(),
                runtime_policy_engine=policy_engine,
                tool_registry=EchoOnlyRegistry(tool),
                runtime_tracer=InMemoryTracer(
                    timestamp_provider=lambda: "2026-05-01T00:00:00+00:00"
                ),
                runtime_approval_store=ApprovalStore(tmpdir),
            )

            response = runtime.run(
                AgentRequest(tool="echo", payload={"text": "hola"}, dry_run=True),
                context(),
            )

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertEqual(policy_engine.calls, 1)
        self.assertEqual(tool.calls, 0)

    def test_dry_run_with_augmentation_does_not_execute_tool(self) -> None:
        tool = SpyEchoTool()
        service = AugmentationService(
            proposal_provider=lambda llm_input, agent_request: provider_output(
                {
                    "intent": "echo requested",
                    "suggested_action": "echo",
                    "arguments": {"text": "hola"},
                    "confidence": 0.9,
                }
            )
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = AgentRuntime(
                runtime_policy_engine=CountingPolicyEngine(),
                tool_registry=EchoOnlyRegistry(tool),
                runtime_tracer=InMemoryTracer(
                    timestamp_provider=lambda: "2026-05-01T00:00:00+00:00"
                ),
                runtime_approval_store=ApprovalStore(tmpdir),
                runtime_augmentation_service=service,
            )

            response = runtime.run(request(), context())

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertEqual(response.result["tool"], "echo")
        self.assertEqual(response.result["executed"], False)
        self.assertEqual(response.result["proposal"]["suggested_action"], "echo")
        self.assertEqual(tool.calls, 0)


if __name__ == "__main__":
    unittest.main()
