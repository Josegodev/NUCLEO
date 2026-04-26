import unittest

from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agent import run_agent
from app.main import app
from app.policies.engine import PolicyEngine
from app.policies.models import PolicyDecision
from app.runtime.orchestrator import AgentRuntime
from app.runtime.planner import Planner
from app.runtime.tracing import InMemoryTracer
from app.schemas.context import ExecutionContext
from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse


class StaticPlanner:
    def __init__(self, plan) -> None:
        self._plan = plan

    def create_plan(self, request: AgentRequest):
        return self._plan


class StaticPolicyEngine:
    def __init__(self, decision: str = "allow", reason: str = "test") -> None:
        self._decision = decision
        self._reason = reason
        self.calls = 0

    def evaluate(self, tool_name: str, payload: dict, dry_run: bool, context: ExecutionContext) -> PolicyDecision:
        self.calls += 1
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


def planned_action(tool_name: str, payload: dict | None = None) -> PlannedAction:
    return PlannedAction(
        tool_name=tool_name,
        payload=payload or {},
        status="planned",
        reason="test plan",
        source="test",
        confidence=1.0,
    )


class RuntimeTracingTests(unittest.TestCase):
    def test_allowed_execution_records_planner_policy_tool(self) -> None:
        tool = SpyTool()
        runtime_tracer = tracer()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner(planned_action("spy", {"x": 1})),
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
            runtime_planner=StaticPlanner(planned_action("spy")),
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
            runtime_planner=StaticPlanner(planned_action("system_info")),
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

    def test_unknown_tool_proposed_by_planner_is_blocked_by_policy(self) -> None:
        runtime_tracer = tracer()
        policy_engine = StaticPolicyEngine("deny", "tool 'missing' is not allowed by policy")
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner(planned_action("missing")),
            runtime_policy_engine=policy_engine,
            tool_registry=StaticRegistry(None),
            runtime_tracer=runtime_tracer,
        )

        response = runtime.run(AgentRequest(dry_run=False), context())
        trace = runtime_tracer.get_trace("trace-req-1")

        self.assertEqual(response.status, "blocked")
        self.assertEqual(policy_engine.calls, 1)
        self.assertEqual([step.phase for step in trace.steps], ["planner", "policy"])
        self.assertEqual(trace.steps[1].status, "denied")
        self.assertIn("not allowed by policy", trace.steps[1].error)

    def test_tracer_failure_does_not_execute_denied_tool(self) -> None:
        tool = SpyTool()
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner(planned_action("spy")),
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
            runtime_planner=StaticPlanner(planned_action("spy")),
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

    def test_health_alias_route_is_registered(self) -> None:
        paths = {route.path for route in app.routes}

        self.assertIn("/", paths)
        self.assertIn("/health", paths)

    def test_runtime_audit_ui_cors_is_local_only(self) -> None:
        cors = next(middleware for middleware in app.user_middleware if middleware.cls is CORSMiddleware)

        self.assertEqual(
            cors.kwargs["allow_origins"],
            [
                "http://127.0.0.1:8766",
                "http://127.0.0.1:8767",
                "http://localhost:8766",
                "http://localhost:8767",
            ],
        )
        self.assertEqual(cors.kwargs["allow_methods"], ["GET", "POST", "OPTIONS"])
        self.assertEqual(cors.kwargs["allow_headers"], ["Authorization", "Content-Type"])

    def test_policy_denies_registered_tool_not_in_explicit_allowlist(self) -> None:
        decision = PolicyEngine(tool_registry=StaticRegistry(SpyTool())).evaluate(
            tool_name="spy",
            payload={},
            dry_run=True,
            context=context(),
        )

        self.assertEqual(decision.decision, "deny")
        self.assertIn("not allowed by policy", decision.reason)

    def test_policy_allows_disk_info_for_authenticated_context(self) -> None:
        decision = PolicyEngine().evaluate(
            tool_name="disk_info",
            payload={},
            dry_run=True,
            context=context(),
        )

        self.assertEqual(decision.decision, "allow")

    def test_policy_decision_rejects_unknown_decision_value(self) -> None:
        with self.assertRaises(ValueError):
            PolicyDecision(decision="unknown", reason="invalid policy result")

    def test_known_input_returns_expected_planner_result(self) -> None:
        result = Planner().create_plan(AgentRequest(user_input="system info", dry_run=True))

        self.assertEqual(result.tool_name, "system_info")
        self.assertEqual(result.status, "planned")
        self.assertEqual(result.source, "rule:system_info")

    def test_unknown_input_returns_no_plan_and_no_execution(self) -> None:
        result = Planner().create_plan(AgentRequest(user_input="unmapped request", dry_run=True))

        self.assertIsNone(result.tool_name)
        self.assertEqual(result.status, "no_plan")
        self.assertIn("No deterministic planner rule", result.reason)

        tool = SpyTool()
        policy_engine = StaticPolicyEngine("allow", "allowed")
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner(result),
            runtime_policy_engine=policy_engine,
            tool_registry=StaticRegistry(tool),
            runtime_tracer=tracer(),
        )
        response = runtime.run(AgentRequest(dry_run=False), context())

        self.assertEqual(response.status, "no_plan")
        self.assertEqual(policy_engine.calls, 0)
        self.assertEqual(tool.calls, 0)

    def test_planner_preserves_valid_payload(self) -> None:
        result = Planner().create_plan(
            AgentRequest(tool="echo", payload={"text": "hello"}, dry_run=True)
        )

        self.assertEqual(result.tool_name, "echo")
        self.assertEqual(result.payload, {"text": "hello"})

    def test_planner_does_not_plan_unregistered_explicit_tool(self) -> None:
        result = Planner(tool_registry=StaticRegistry(None)).create_plan(
            AgentRequest(tool="missing", payload={}, dry_run=True)
        )

        self.assertEqual(result.status, "no_plan")
        self.assertIsNone(result.tool_name)
        self.assertIn("not registered", result.reason)

    def test_runtime_stops_before_policy_when_planner_result_is_invalid(self) -> None:
        tool = SpyTool()
        policy_engine = StaticPolicyEngine("allow", "allowed")
        runtime = AgentRuntime(
            runtime_planner=StaticPlanner({"tool": "spy", "payload": {}}),
            runtime_policy_engine=policy_engine,
            tool_registry=StaticRegistry(tool),
            runtime_tracer=tracer(),
        )

        response = runtime.run(AgentRequest(dry_run=False), context())

        self.assertEqual(response.status, "error")
        self.assertEqual(policy_engine.calls, 0)
        self.assertEqual(tool.calls, 0)

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
