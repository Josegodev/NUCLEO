import unittest

from app.policies.engine import PolicyEngine
from app.policies.models import (
    PolicyDecision,
    PolicyDecisionValue,
    PolicyValidatedField,
)
from app.runtime.orchestrator import AgentRuntime
from app.runtime.tracing import InMemoryTracer
from app.schemas.context import ExecutionContext
from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentRequest
from app.schemas.responses import ExecutionErrorCode, ExecutionStatus
from app.tools.base import BaseTool
from app.tools.local.echo_tool import EchoTool
from app.tools.registry import ToolRegistry


class StaticPlanner:
    def __init__(self, plan: PlannedAction) -> None:
        self._plan = plan

    def create_plan(self, request):
        return self._plan


class StaticPolicyEngine:
    def __init__(self, decision) -> None:
        self._decision = decision
        self.calls = 0

    def evaluate(self, tool_name: str, payload: dict, dry_run: bool, context):
        self.calls += 1
        return self._decision


class CountingRegistry:
    def __init__(self, tool: BaseTool | None) -> None:
        self._tool = tool
        self.get_calls = 0

    def get(self, tool_name: str):
        self.get_calls += 1
        if self._tool is not None and tool_name == self._tool.name:
            return self._tool
        return None


class SpyEchoTool(EchoTool):
    def __init__(self) -> None:
        self.calls = 0

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        self.calls += 1
        return super().run(payload, context=context)


class RejectingInputEchoTool(SpyEchoTool):
    def validate_input(self, payload: dict | None = None) -> dict:
        raise ValueError("invalid test payload")


class ToolWithoutContract(BaseTool):
    name = "echo"
    description = "Missing contract."
    read_only = True
    risk_level = "low"


class ToolOutsideClosedSet(BaseTool):
    name = "not_registered"
    description = "Outside closed production tool set."
    read_only = True
    risk_level = "low"
    contract = EchoTool.contract


def context() -> ExecutionContext:
    return ExecutionContext(
        user_id="u1",
        username="tester",
        roles=["admin"],
        authenticated=True,
        request_id="policy-tool-contract",
    )


def tracer() -> InMemoryTracer:
    return InMemoryTracer(timestamp_provider=lambda: "2026-05-02T00:00:00+00:00")


def echo_plan(payload: dict | None = None) -> PlannedAction:
    return PlannedAction(
        tool_name="echo",
        payload=payload or {"text": "hola"},
        status="planned",
        confidence=1.0,
        reason="contract test plan",
        source="explicit_request",
    )


def policy_decision(decision: PolicyDecisionValue, reason: str) -> PolicyDecision:
    return PolicyDecision(
        decision=decision,
        reason=reason,
        validated_fields=[
            PolicyValidatedField.AUTHENTICATED_CONTEXT,
            PolicyValidatedField.TOOL_NAME,
        ],
    )


class PolicyToolContractTests(unittest.TestCase):
    def test_policy_denial_stops_before_registry_and_tool_execution(self) -> None:
        tool = SpyEchoTool()
        registry = CountingRegistry(tool)
        runtime_tracer = tracer()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner(echo_plan()),
            runtime_policy_engine=StaticPolicyEngine(
                policy_decision(PolicyDecisionValue.DENY, "blocked by policy")
            ),
            tool_registry=registry,
            runtime_tracer=runtime_tracer,
        )

        response = runtime.run(request=AgentRequest(dry_run=False), context=context())
        trace = runtime_tracer.get_trace("trace-policy-tool-contract")

        self.assertEqual(response.status, ExecutionStatus.REJECTED)
        self.assertEqual(response.errors[0].code, ExecutionErrorCode.POLICY_DENIED)
        self.assertIn("blocked by policy", response.errors[0].message)
        self.assertEqual(registry.get_calls, 0)
        self.assertEqual(tool.calls, 0)
        self.assertEqual([step.phase for step in trace.steps], ["planner", "policy"])
        self.assertEqual(trace.steps[1].status, "denied")

    def test_unknown_tool_after_policy_allow_returns_controlled_error(self) -> None:
        registry = CountingRegistry(None)
        runtime_tracer = tracer()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner(echo_plan()),
            runtime_policy_engine=StaticPolicyEngine(
                policy_decision(PolicyDecisionValue.ALLOW, "allowed by test")
            ),
            tool_registry=registry,
            runtime_tracer=runtime_tracer,
        )

        response = runtime.run(request=AgentRequest(dry_run=False), context=context())
        trace = runtime_tracer.get_trace("trace-policy-tool-contract")

        self.assertEqual(response.status, ExecutionStatus.ERROR)
        self.assertEqual(response.errors[0].code, ExecutionErrorCode.TOOL_NOT_FOUND)
        self.assertIn("unknown tool", response.errors[0].message)
        self.assertEqual(registry.get_calls, 1)
        self.assertEqual([step.phase for step in trace.steps], ["planner", "policy", "registry"])
        self.assertEqual(trace.steps[2].status, "error")
        self.assertFalse(trace.steps[2].output["found"])

    def test_default_policy_engine_uses_runtime_registry(self) -> None:
        registry = CountingRegistry(None)
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner(echo_plan()),
            tool_registry=registry,
            runtime_tracer=tracer(),
        )

        response = runtime.run(request=AgentRequest(dry_run=False), context=context())

        self.assertEqual(response.status, ExecutionStatus.REJECTED)
        self.assertEqual(response.errors[0].code, ExecutionErrorCode.POLICY_DENIED)
        self.assertIn("is not registered", response.errors[0].message)
        self.assertEqual(registry.get_calls, 1)

    def test_policy_denies_invalid_echo_payloads(self) -> None:
        cases = [
            {},
            {"other": "hola"},
            {"text": ""},
            {"text": "hola", "extra": True},
        ]

        for payload in cases:
            with self.subTest(payload=payload):
                decision = PolicyEngine().evaluate(
                    tool_name="echo",
                    payload=payload,
                    dry_run=True,
                    context=context(),
                )

                self.assertEqual(decision.decision, PolicyDecisionValue.DENY)
                self.assertIn("payload does not match tool contract", decision.reason)
                self.assertIn(PolicyValidatedField.PAYLOAD, decision.validated_fields)

    def test_runtime_tool_input_validation_blocks_execution_after_policy_allow(self) -> None:
        tool = RejectingInputEchoTool()
        registry = CountingRegistry(tool)
        runtime_tracer = tracer()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner(echo_plan()),
            runtime_policy_engine=StaticPolicyEngine(
                policy_decision(PolicyDecisionValue.ALLOW, "allowed by test")
            ),
            tool_registry=registry,
            runtime_tracer=runtime_tracer,
        )

        response = runtime.run(request=AgentRequest(dry_run=False), context=context())
        trace = runtime_tracer.get_trace("trace-policy-tool-contract")

        self.assertEqual(response.status, ExecutionStatus.REJECTED)
        self.assertEqual(response.errors[0].code, ExecutionErrorCode.TOOL_INPUT_INVALID)
        self.assertIn("Tool input does not match contract", response.errors[0].message)
        self.assertEqual(tool.calls, 0)
        self.assertEqual([step.phase for step in trace.steps], ["planner", "policy", "registry", "tool"])
        self.assertEqual(trace.steps[3].status, "error")
        self.assertIn("invalid test payload", trace.steps[3].error)

    def test_valid_echo_payload_executes_once(self) -> None:
        tool = SpyEchoTool()
        registry = CountingRegistry(tool)
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner(echo_plan({"text": "hola"})),
            runtime_policy_engine=PolicyEngine(tool_registry=registry),
            tool_registry=registry,
            runtime_tracer=tracer(),
        )

        response = runtime.run(request=AgentRequest(dry_run=False), context=context())

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertEqual(response.result["echo"], {"text": "hola"})
        self.assertEqual(tool.calls, 1)

    def test_invalid_policy_result_stops_before_registry_and_tool(self) -> None:
        tool = SpyEchoTool()
        registry = CountingRegistry(tool)
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner(echo_plan()),
            runtime_policy_engine=StaticPolicyEngine({"decision": "allow"}),
            tool_registry=registry,
            runtime_tracer=tracer(),
        )

        response = runtime.run(request=AgentRequest(dry_run=False), context=context())

        self.assertEqual(response.status, ExecutionStatus.ERROR)
        self.assertEqual(response.errors[0].code, ExecutionErrorCode.POLICY_INVALID_RESULT)
        self.assertEqual(registry.get_calls, 0)
        self.assertEqual(tool.calls, 0)

    def test_tool_registry_rejects_duplicate_names(self) -> None:
        registry = ToolRegistry()
        registry.register(EchoTool())

        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register(EchoTool())

    def test_tool_registry_rejects_tool_without_contract(self) -> None:
        registry = ToolRegistry()

        with self.assertRaisesRegex(TypeError, "ToolContractArtifact"):
            registry.register(ToolWithoutContract())

    def test_tool_registry_rejects_name_outside_closed_tool_set(self) -> None:
        registry = ToolRegistry()

        with self.assertRaisesRegex(ValueError, "outside the closed tool set"):
            registry.register(ToolOutsideClosedSet())

    def test_policy_tool_contract_sources_do_not_import_runtime_lab_directly(self) -> None:
        source_paths = [
            "app/policies/engine.py",
            "app/tools/registry.py",
            "app/tools/base.py",
            "app/schemas/artifacts.py",
        ]

        for source_path in source_paths:
            with self.subTest(source_path=source_path):
                with open(source_path, encoding="utf-8") as source_file:
                    self.assertNotIn("runtime_lab", source_file.read())


if __name__ == "__main__":
    unittest.main()
