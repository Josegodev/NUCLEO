import unittest

from app.api.routes.agent import run_agent
from app.main import app
from app.policies.models import PolicyDecision
from app.runtime.orchestrator import AgentRuntime
from app.runtime.tracing import InMemoryTracer
from app.schemas.context import ExecutionContext
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse


class StaticPlanner:
    def __init__(self, plan: dict) -> None:
        self._plan = plan

    def create_plan(self, request: AgentRequest) -> dict:
        return self._plan


class StaticPolicyEngine:
    def __init__(self, decision: str = "allow", reason: str = "test") -> None:
        self._decision = decision
        self._reason = reason

    def evaluate(self, tool_name: str, payload: dict, dry_run: bool, context: ExecutionContext) -> PolicyDecision:
        return PolicyDecision(decision=self._decision, reason=self._reason)


class SpyTool:
    name = "spy"
    description = "Test spy tool."
    read_only = True
    risk_level = "low"

    def __init__(self, fail: bool = False) -> None:
        self.calls = 0
        self.fail = fail

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        self.calls += 1
        if self.fail:
            raise RuntimeError("tool failed")
        return {"ok": True, "payload": payload}


class StaticRegistry:
    def __init__(self, tool: SpyTool | None) -> None:
        self._tool = tool

    def get(self, tool_name: str):
        if self._tool and tool_name == self._tool.name:
            return self._tool
        return None

    def list_tools(self) -> list:
        return [self._tool] if self._tool else []


class FailingTracer:
    def start_trace(self, request_id: str | None = None):
        raise RuntimeError("tracer unavailable")

    def record_step(self, trace, step):
        raise RuntimeError("tracer unavailable")

    def get_trace(self, trace_id: str):
        return None


def context() -> ExecutionContext:
    return ExecutionContext(
        user_id="u1",
        username="tester",
        roles=["admin"],
        authenticated=True,
        request_id="req-1",
    )


def tracer() -> InMemoryTracer:
    return InMemoryTracer(timestamp_provider=lambda: "2026-04-25T00:00:00+00:00")


class RuntimeTracingTests(unittest.TestCase):
    def test_allowed_execution_records_planner_policy_tool(self) -> None:
        tool = SpyTool()
        runtime_tracer = tracer()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner({"tool": "spy", "payload": {"x": 1}}),
            runtime_policy_engine=StaticPolicyEngine("allow", "allowed"),
            tool_registry=StaticRegistry(tool),
            runtime_tracer=runtime_tracer,
        )

        response = runtime.run(AgentRequest(dry_run=False), context())
        trace = runtime_tracer.get_trace("trace-req-1")

        self.assertEqual(response.status, "success")
        self.assertEqual(tool.calls, 1)
        self.assertEqual([step.phase for step in trace.steps], ["planner", "policy", "registry", "tool"])
        self.assertEqual([step.status for step in trace.steps], ["success", "success", "success", "success"])

    def test_denied_execution_records_planner_policy_and_does_not_run_tool(self) -> None:
        tool = SpyTool()
        runtime_tracer = tracer()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner({"tool": "spy", "payload": {}}),
            runtime_policy_engine=StaticPolicyEngine("deny", "blocked by test"),
            tool_registry=StaticRegistry(tool),
            runtime_tracer=runtime_tracer,
        )

        response = runtime.run(AgentRequest(dry_run=False), context())
        trace = runtime_tracer.get_trace("trace-req-1")

        self.assertEqual(response.status, "blocked")
        self.assertEqual(tool.calls, 0)
        self.assertEqual([step.phase for step in trace.steps], ["planner", "policy"])
        self.assertEqual(trace.steps[1].status, "denied")

    def test_dry_run_with_system_info_records_registry_and_skipped_tool(self) -> None:
        tool = SpyTool()
        tool.name = "system_info"
        runtime_tracer = tracer()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner({"tool": "system_info", "payload": {}}),
            runtime_policy_engine=StaticPolicyEngine("allow", "allowed"),
            tool_registry=StaticRegistry(tool),
            runtime_tracer=runtime_tracer,
        )

        response = runtime.run(AgentRequest(user_input="system info", dry_run=True), context())
        trace = runtime_tracer.get_trace("trace-req-1")

        self.assertEqual(response.status, "dry_run_success")
        self.assertEqual(tool.calls, 0)
        self.assertEqual([step.phase for step in trace.steps], ["planner", "policy", "registry", "tool"])
        self.assertEqual(trace.steps[3].status, "skipped")
        self.assertEqual(trace.steps[3].output["executed"], False)
        self.assertEqual(trace.steps[3].output["reason"], "dry_run")

    def test_unknown_tool_resolution_is_traced_as_error(self) -> None:
        runtime_tracer = tracer()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner({"tool": "missing", "payload": {}}),
            runtime_policy_engine=StaticPolicyEngine("allow", "allowed"),
            tool_registry=StaticRegistry(None),
            runtime_tracer=runtime_tracer,
        )

        response = runtime.run(AgentRequest(dry_run=False), context())
        trace = runtime_tracer.get_trace("trace-req-1")

        self.assertEqual(response.status, "error")
        self.assertEqual([step.phase for step in trace.steps], ["planner", "policy", "registry"])
        self.assertEqual(trace.steps[2].status, "error")
        self.assertIn("unknown tool", trace.steps[2].error)

    def test_tracer_failure_does_not_execute_denied_tool(self) -> None:
        tool = SpyTool()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner({"tool": "spy", "payload": {}}),
            runtime_policy_engine=StaticPolicyEngine("deny", "blocked by test"),
            tool_registry=StaticRegistry(tool),
            runtime_tracer=FailingTracer(),
        )

        response = runtime.run(AgentRequest(dry_run=False), context())

        self.assertEqual(response.status, "blocked")
        self.assertEqual(tool.calls, 0)

    def test_tool_error_is_traced_and_propagated(self) -> None:
        tool = SpyTool(fail=True)
        runtime_tracer = tracer()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner({"tool": "spy", "payload": {}}),
            runtime_policy_engine=StaticPolicyEngine("allow", "allowed"),
            tool_registry=StaticRegistry(tool),
            runtime_tracer=runtime_tracer,
        )

        with self.assertRaises(RuntimeError):
            runtime.run(AgentRequest(dry_run=False), context())

        trace = runtime_tracer.get_trace("trace-req-1")
        self.assertEqual(trace.steps[3].phase, "tool")
        self.assertEqual(trace.steps[3].status, "error")
        self.assertEqual(trace.steps[3].error, "tool failed")

    def test_api_response_contract_does_not_gain_trace_id(self) -> None:
        fields = set(AgentResponse.model_fields)

        self.assertEqual(fields, {"status", "message", "result"})

    def test_agent_run_endpoint_contract_for_valid_dry_run(self) -> None:
        route = next(
            route
            for route in app.routes
            if getattr(route, "path", None) == "/agent/run"
            and "POST" in getattr(route, "methods", set())
        )

        response = run_agent(
            AgentRequest(user_input="system info", dry_run=True),
            context=ExecutionContext(
                user_id="jose",
                username="jose",
                roles=["admin"],
                authenticated=True,
                request_id="endpoint-test",
            ),
        )

        self.assertEqual(route.status_code, None)
        self.assertEqual(response.status, "dry_run_success")
        self.assertEqual(response.result["executed"], False)
        self.assertEqual(response.result["tool"], "system_info")


if __name__ == "__main__":
    unittest.main()
