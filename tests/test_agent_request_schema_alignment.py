import json
import tempfile
import unittest

from pydantic import ValidationError

from app.adapters.model_router import (
    DEFAULT_LOCAL_MODEL_ID,
    ModelBackendCall,
    ModelRouter,
)
from app.api.routes import agent as agent_route
from app.policies.models import (
    PolicyDecision,
    PolicyDecisionValue,
    PolicyValidatedField,
)
from app.runtime.augmentation_service import AugmentationService
from app.runtime.orchestrator import AgentRuntime
from app.runtime.tracing import InMemoryTracer
from app.schemas.context import ExecutionContext
from app.schemas.requests import AgentBackend, AgentMode, AgentRequest
from app.schemas.responses import AgentResponse, ExecutionStatus
from app.services.approval.approval_store import ApprovalStore
from app.tools.local.echo_tool import EchoTool


def frontend_payload(model_id: str | None = "qwen", dry_run: bool = True) -> dict:
    payload = {
        "input": "haz echo de hola",
        "agent_mode": "proposal_only",
        "dry_run": dry_run,
    }
    if model_id is not None:
        payload["augmentation"] = {"model_id": model_id}
    return payload


def valid_echo_output() -> str:
    return json.dumps(
        {
            "intent": "echo requested",
            "suggested_action": "echo",
            "arguments": {"text": "hola"},
            "confidence": 0.9,
        }
    )


def context() -> ExecutionContext:
    return ExecutionContext(
        user_id="jose",
        username="jose",
        roles=["admin"],
        authenticated=True,
        request_id="schema-alignment-test",
        api_key_name="local_jose_dev",
    )


def tracer() -> InMemoryTracer:
    return InMemoryTracer(timestamp_provider=lambda: "2026-05-02T00:00:00+00:00")


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
            validated_fields=[
                PolicyValidatedField.TOOL_NAME,
                PolicyValidatedField.DRY_RUN,
            ],
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


class RecordingAgentService:
    def __init__(self) -> None:
        self.request = None

    def run(self, request, context) -> AgentResponse:
        self.request = request
        return AgentResponse(
            status=ExecutionStatus.SUCCESS,
            result={
                "dry_run": request.dry_run,
                "agent_mode": request.agent_mode.value if request.agent_mode else None,
                "model_id": request.options.model_id if request.options else None,
            },
            trace_id="trace-schema-alignment",
        )


class AgentRequestSchemaAlignmentTests(unittest.TestCase):
    def test_agent_request_accepts_root_agent_mode_proposal_only(self) -> None:
        request = AgentRequest.model_validate(
            {
                "input": "haz echo de hola",
                "agent_mode": "proposal_only",
                "dry_run": False,
            }
        )

        self.assertEqual(request.agent_mode, AgentMode.PROPOSAL_ONLY)
        self.assertEqual(request.options.agent_mode, AgentMode.PROPOSAL_ONLY)
        self.assertTrue(request.dry_run)

    def test_agent_request_accepts_root_augmentation_model_id(self) -> None:
        request = AgentRequest.model_validate(frontend_payload("qwen"))

        self.assertEqual(request.augmentation.model_id, "qwen")
        self.assertEqual(request.options.model_id, "qwen")

    def test_blank_augmentation_model_id_uses_default_model(self) -> None:
        request = AgentRequest.model_validate(frontend_payload(""))

        self.assertIsNone(request.augmentation.model_id)
        self.assertEqual(request.options.model_id, DEFAULT_LOCAL_MODEL_ID)

    def test_invalid_augmentation_model_id_falls_back_in_request(self) -> None:
        request = AgentRequest.model_validate(frontend_payload("not-allowed"))

        self.assertEqual(request.augmentation.model_id, DEFAULT_LOCAL_MODEL_ID)
        self.assertEqual(request.options.model_id, DEFAULT_LOCAL_MODEL_ID)
        self.assertIn("not allowed", request.model_resolution_reason)

    def test_agent_request_rejects_unknown_extra_fields(self) -> None:
        with self.assertRaises(ValidationError):
            AgentRequest.model_validate(
                {
                    **frontend_payload("qwen"),
                    "unexpected": True,
                }
            )

    def test_invalid_model_id_falls_back_before_provider_call(self) -> None:
        calls: list[str] = []

        def local_caller(model_id: str, prompt: str) -> ModelBackendCall:
            calls.append(model_id)
            return ModelBackendCall(
                backend_used=AgentBackend.LOCAL,
                model_used=model_id,
                success=True,
                output=valid_echo_output(),
                latency_ms=1.0,
            )

        result = ModelRouter(local_caller=local_caller).generate(
            prompt="proposal prompt",
            backend=AgentBackend.LOCAL,
            model_id="not-allowed",
        )

        self.assertEqual(calls, [DEFAULT_LOCAL_MODEL_ID])
        self.assertEqual(result["model_used"], DEFAULT_LOCAL_MODEL_ID)
        self.assertTrue(result["fallback_used"])
        self.assertIn("not allowed", result["fallback_reason"])

    def test_agent_run_route_accepts_frontend_payload_without_422(self) -> None:
        original_agent_service = agent_route.agent_service
        service = RecordingAgentService()
        agent_route.agent_service = service
        try:
            response = agent_route.run_agent(
                AgentRequest.model_validate(frontend_payload("qwen")),
                context=context(),
            )
        finally:
            agent_route.agent_service = original_agent_service

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertEqual(response.result["agent_mode"], "proposal_only")
        self.assertEqual(response.result["model_id"], "qwen")
        self.assertEqual(service.request.options.model_id, "qwen")

    def test_frontend_proposal_payload_keeps_dry_run_from_executing_tool(self) -> None:
        tool = SpyEchoTool()
        service = AugmentationService(
            proposal_provider=lambda llm_input, agent_request: valid_echo_output()
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = AgentRuntime(
                runtime_policy_engine=CountingPolicyEngine(),
                tool_registry=EchoOnlyRegistry(tool),
                runtime_tracer=tracer(),
                runtime_approval_store=ApprovalStore(tmpdir),
                runtime_augmentation_service=service,
            )
            response = runtime.run(
                AgentRequest.model_validate(frontend_payload("qwen", dry_run=False)),
                context(),
            )

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertTrue(response.result["dry_run"])
        self.assertFalse(response.result["executed"])
        self.assertEqual(response.result["tool"], "echo")
        self.assertEqual(response.result["model_id"], "qwen")
        self.assertEqual(tool.calls, 0)


if __name__ == "__main__":
    unittest.main()
