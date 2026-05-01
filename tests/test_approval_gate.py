import tempfile
import unittest

from app.policies.models import (
    PolicyDecision,
    PolicyDecisionValue,
    PolicyValidatedField,
)
from app.main import app
from app.runtime.orchestrator import AgentRuntime
from app.runtime.tracing import InMemoryTracer
from app.schemas.approval import ExecutionState
from app.schemas.context import ExecutionContext
from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentRequest
from app.schemas.responses import ExecutionStatus
from app.services.approval.approval_store import ApprovalStore
from app.tools.local.echo_tool import EchoTool


class CountingPlanner:
    def __init__(self) -> None:
        self.calls = 0

    def create_plan(self, request: AgentRequest) -> PlannedAction:
        self.calls += 1
        return PlannedAction(
            tool_name="echo",
            payload={"text": "hola"},
            status="planned",
            confidence=0.9,
            reason="test proposal",
            source="llm_assisted",
            metadata={
                "proposal": {
                    "intent": "echo requested",
                    "suggested_action": "echo",
                    "arguments": {"text": "hola"},
                    "confidence": 0.9,
                }
            },
        )


class FailingPlanner:
    def create_plan(self, request: AgentRequest) -> PlannedAction:
        raise AssertionError("approve must not call Planner or LLM")


class CountingPolicyEngine:
    def __init__(self, decisions: list[PolicyDecisionValue] | None = None) -> None:
        self.calls = 0
        self.decisions = decisions or [PolicyDecisionValue.ALLOW]

    def evaluate(
        self,
        tool_name: str,
        payload: dict,
        dry_run: bool,
        context: ExecutionContext,
    ) -> PolicyDecision:
        decision = self.decisions[min(self.calls, len(self.decisions) - 1)]
        self.calls += 1
        return PolicyDecision(
            decision=decision,
            reason=f"policy {decision.value}",
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


class InvalidPayloadEchoTool(SpyEchoTool):
    def validate_input(self, payload: dict | None = None) -> dict:
        raise ValueError("invalid test payload")


class StaticRegistry:
    def __init__(self, tool) -> None:
        self._tool = tool
        self.get_calls = 0

    def get(self, tool_name: str):
        self.get_calls += 1
        if tool_name == self._tool.name:
            return self._tool
        return None


def context() -> ExecutionContext:
    return ExecutionContext(
        user_id="u1",
        username="tester",
        roles=["admin"],
        authenticated=True,
        request_id="approval-gate-test",
    )


def tracer() -> InMemoryTracer:
    return InMemoryTracer(timestamp_provider=lambda: "2026-05-01T00:00:00+00:00")


def proposal_request() -> AgentRequest:
    return AgentRequest.model_validate(
        {
            "input": "say hola",
            "context": {},
            "options": {
                "backend": "auto",
                "model_id": "llama3.1:8b",
                "agent_mode": "proposal_only",
                "dry_run": True,
            },
        }
    )


class ApprovalGateTests(unittest.TestCase):
    def test_approve_endpoint_is_registered_on_real_agent_router(self) -> None:
        paths = {route.path for route in app.routes}

        self.assertIn("/agent/approve", paths)

    def make_runtime(
        self,
        store: ApprovalStore,
        planner: CountingPlanner | None = None,
        policy_engine: CountingPolicyEngine | None = None,
        tool: SpyEchoTool | None = None,
    ) -> tuple[AgentRuntime, CountingPlanner, CountingPolicyEngine, SpyEchoTool]:
        planner = planner or CountingPlanner()
        policy_engine = policy_engine or CountingPolicyEngine()
        tool = tool or SpyEchoTool()
        runtime = AgentRuntime(
            runtime_planner=planner,
            runtime_policy_engine=policy_engine,
            tool_registry=StaticRegistry(tool),
            runtime_tracer=tracer(),
            runtime_approval_store=store,
        )
        return runtime, planner, policy_engine, tool

    def test_dry_run_proposal_is_persisted_with_trace_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ApprovalStore(tmpdir)
            runtime, _, _, _ = self.make_runtime(store)

            response = runtime.run(proposal_request(), context())
            record = store.get(response.trace_id)

            self.assertEqual(response.status, ExecutionStatus.SUCCESS)
            self.assertIsNotNone(record)
            self.assertEqual(record.execution_state, ExecutionState.PROPOSED)
            self.assertEqual(record.proposed_tool, "echo")

    def test_reject_marks_rejected_and_does_not_run_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ApprovalStore(tmpdir)
            runtime, _, _, tool = self.make_runtime(store)
            response = runtime.run(proposal_request(), context())

            approval = runtime.approve(response.trace_id, approved=False, context=context())

            self.assertEqual(approval.status, "success")
            self.assertEqual(approval.execution_state, ExecutionState.REJECTED)
            self.assertFalse(approval.executed)
            self.assertEqual(tool.calls, 0)

    def test_approve_does_not_call_planner_again(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ApprovalStore(tmpdir)
            runtime, planner, _, tool = self.make_runtime(store)
            response = runtime.run(proposal_request(), context())

            approval = runtime.approve(response.trace_id, approved=True, context=context())

            self.assertEqual(approval.execution_state, ExecutionState.EXECUTED)
            self.assertEqual(planner.calls, 1)
            self.assertEqual(tool.calls, 1)

    def test_approve_does_not_call_planner_or_llm_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ApprovalStore(tmpdir)
            proposal_runtime, _, _, _ = self.make_runtime(store)
            response = proposal_runtime.run(proposal_request(), context())
            approval_runtime = AgentRuntime(
                runtime_planner=FailingPlanner(),
                runtime_policy_engine=CountingPolicyEngine(),
                tool_registry=StaticRegistry(SpyEchoTool()),
                runtime_tracer=tracer(),
                runtime_approval_store=store,
            )

            approval = approval_runtime.approve(
                response.trace_id,
                approved=True,
                context=context(),
            )

            self.assertEqual(approval.execution_state, ExecutionState.EXECUTED)

    def test_approve_reevaluates_policy_engine(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ApprovalStore(tmpdir)
            policy = CountingPolicyEngine(
                [PolicyDecisionValue.ALLOW, PolicyDecisionValue.ALLOW]
            )
            runtime, _, policy, _ = self.make_runtime(store, policy_engine=policy)
            response = runtime.run(proposal_request(), context())

            runtime.approve(response.trace_id, approved=True, context=context())

            self.assertEqual(policy.calls, 2)

    def test_policy_deny_prevents_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ApprovalStore(tmpdir)
            policy = CountingPolicyEngine(
                [PolicyDecisionValue.ALLOW, PolicyDecisionValue.DENY]
            )
            runtime, _, policy, tool = self.make_runtime(store, policy_engine=policy)
            response = runtime.run(proposal_request(), context())

            approval = runtime.approve(response.trace_id, approved=True, context=context())

            self.assertEqual(approval.status, "denied")
            self.assertEqual(approval.execution_state, ExecutionState.DENIED)
            self.assertEqual(policy.calls, 2)
            self.assertEqual(tool.calls, 0)

    def test_missing_trace_id_returns_controlled_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ApprovalStore(tmpdir)
            runtime, _, _, _ = self.make_runtime(store)

            approval = runtime.approve("trace-missing", approved=True, context=context())

            self.assertEqual(approval.status, "error")
            self.assertEqual(approval.execution_state, ExecutionState.ERROR)
            self.assertFalse(approval.executed)

    def test_payload_validation_failure_prevents_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ApprovalStore(tmpdir)
            runtime, _, _, _ = self.make_runtime(store)
            response = runtime.run(proposal_request(), context())

            failing_runtime, _, _, failing_tool = self.make_runtime(
                store,
                tool=InvalidPayloadEchoTool(),
            )
            approval = failing_runtime.approve(
                response.trace_id,
                approved=True,
                context=context(),
            )

            self.assertEqual(approval.status, "error")
            self.assertEqual(approval.execution_state, ExecutionState.ERROR)
            self.assertFalse(approval.executed)
            self.assertEqual(failing_tool.calls, 0)

    def test_approve_executes_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ApprovalStore(tmpdir)
            runtime, _, _, tool = self.make_runtime(store)
            response = runtime.run(proposal_request(), context())

            first = runtime.approve(response.trace_id, approved=True, context=context())
            second = runtime.approve(response.trace_id, approved=True, context=context())

            self.assertEqual(first.execution_state, ExecutionState.EXECUTED)
            self.assertEqual(second.execution_state, ExecutionState.EXECUTED)
            self.assertTrue(second.executed)
            self.assertEqual(tool.calls, 1)


if __name__ == "__main__":
    unittest.main()
