import json
import unittest

from app.policies.models import (
    PolicyDecision,
    PolicyDecisionValue,
    PolicyValidatedField,
)
from app.runtime.orchestrator import AgentRuntime
from app.runtime.planner import DeterministicPlannerStrategy, Planner
from app.runtime.planner_augmentation import (
    LLMAssistedPlannerStrategy,
    LLMPlanOutputValidator,
    build_tool_contract_prompt,
)
from app.runtime.tracing import InMemoryTracer
from app.schemas.context import ExecutionContext
from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentRequest, AgentRunOptions
from app.schemas.responses import ExecutionStatus
from app.tools.local.echo_tool import EchoTool
from app.tools.registry import registry as production_registry


class SpyEchoTool(EchoTool):
    def __init__(self) -> None:
        self.calls = 0

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        self.calls += 1
        return super().run(payload, context=context)


class SpyRegistry:
    def __init__(self, tool=None) -> None:
        self._tool = tool
        self.get_calls = 0
        self.register_calls = 0

    def get(self, tool_name: str):
        self.get_calls += 1
        if self._tool and tool_name == self._tool.name:
            return self._tool
        return None

    def register(self, tool) -> None:
        self.register_calls += 1
        raise AssertionError("PlannerStrategy must not register tools")


class CountingPolicyEngine:
    def __init__(
        self,
        decision: PolicyDecisionValue = PolicyDecisionValue.ALLOW,
    ) -> None:
        self.calls = 0
        self.decision = decision

    def evaluate(
        self,
        tool_name: str,
        payload: dict,
        dry_run: bool,
        context: ExecutionContext,
    ) -> PolicyDecision:
        self.calls += 1
        return PolicyDecision(
            decision=self.decision,
            reason=f"policy {self.decision.value}",
            validated_fields=[PolicyValidatedField.TOOL_NAME],
        )


def context() -> ExecutionContext:
    return ExecutionContext(
        user_id="u1",
        username="tester",
        roles=["admin"],
        authenticated=True,
        request_id="planner-augmentation-test",
    )


def tracer() -> InMemoryTracer:
    return InMemoryTracer(timestamp_provider=lambda: "2026-05-01T00:00:00+00:00")


def llm_output(payload: dict) -> str:
    return json.dumps(payload)


def valid_echo_payload() -> dict:
    return {
        "intent": "echo was requested",
        "suggested_action": "echo",
        "arguments": {"text": "hola"},
        "confidence": 0.91,
    }


def augmented_request(user_input: str, dry_run: bool = True) -> AgentRequest:
    return AgentRequest(
        user_input=user_input,
        dry_run=dry_run,
        options=AgentRunOptions(),
    )


class PlannerAugmentationTests(unittest.TestCase):
    def test_deterministic_strategy_preserves_existing_behavior(self) -> None:
        result = DeterministicPlannerStrategy().create_plan(
            AgentRequest(user_input="system info", dry_run=True)
        )

        self.assertIsInstance(result, PlannedAction)
        self.assertEqual(result.tool_name, "system_info")
        self.assertEqual(result.status, "planned")
        self.assertEqual(result.source, "rule:system_info")

    def test_planner_default_strategy_is_deterministic(self) -> None:
        result = Planner().create_plan(
            AgentRequest(user_input="system info", dry_run=True)
        )

        self.assertEqual(result.tool_name, "system_info")
        self.assertEqual(result.source, "rule:system_info")

    def test_llm_strategy_rejects_invalid_json_and_falls_back(self) -> None:
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            proposal_provider=lambda llm_input, request: "not-json",
        )

        result = Planner(strategy=strategy).create_plan(augmented_request("system info"))

        self.assertEqual(result.source, "rule:system_info")
        self.assertEqual(strategy.audit_records[0].raw_output, "not-json")
        self.assertFalse(strategy.audit_records[0].accepted)
        self.assertIn("Invalid JSON", strategy.audit_records[0].fallback_reason)

    def test_llm_strategy_rejects_unknown_tool_and_falls_back(self) -> None:
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            proposal_provider=lambda llm_input, request: llm_output(
                {
                    "intent": "invalid tool",
                    "suggested_action": "missing_tool",
                    "arguments": {},
                    "confidence": 0.7,
                }
            ),
        )

        result = Planner(strategy=strategy).create_plan(augmented_request("system info"))

        self.assertEqual(result.source, "rule:system_info")
        self.assertFalse(strategy.audit_records[0].accepted)
        self.assertIn("missing_tool", strategy.audit_records[0].fallback_reason)

    def test_llm_strategy_rejects_invalid_payload_and_falls_back(self) -> None:
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            proposal_provider=lambda llm_input, request: llm_output(
                {
                    "intent": "payload is incomplete",
                    "suggested_action": "echo",
                    "arguments": {},
                    "confidence": 0.7,
                }
            ),
        )

        result = Planner(strategy=strategy).create_plan(augmented_request("system info"))

        self.assertEqual(result.source, "rule:system_info")
        self.assertFalse(strategy.audit_records[0].accepted)
        self.assertIn("payload", strategy.audit_records[0].fallback_reason)

    def test_tool_contract_prompt_includes_real_echo_text_argument(self) -> None:
        prompt = build_tool_contract_prompt(production_registry)

        self.assertIn("- echo", prompt)
        self.assertIn("text: string", prompt)
        self.assertNotIn("message:", prompt)
        self.assertIn("Use EXACT argument names.", prompt)

    def test_llm_strategy_rejects_echo_message_argument_and_falls_back(self) -> None:
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            proposal_provider=lambda llm_input, request: llm_output(
                {
                    "intent": "echo was requested",
                    "suggested_action": "echo",
                    "arguments": {"message": "hola"},
                    "confidence": 0.91,
                }
            ),
        )

        result = Planner(strategy=strategy).create_plan(augmented_request("system info"))

        self.assertEqual(result.source, "rule:system_info")
        self.assertTrue(result.metadata["fallback_used"])
        self.assertIn("message", result.metadata["fallback_reason"])
        self.assertFalse(strategy.audit_records[0].accepted)

    def test_llm_strategy_rejects_incomplete_output_and_falls_back(self) -> None:
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            proposal_provider=lambda llm_input, request: llm_output(
                {
                    "intent": "missing confidence",
                    "suggested_action": "echo",
                    "arguments": {"text": "hola"},
                }
            ),
        )

        result = Planner(strategy=strategy).create_plan(augmented_request("system info"))

        self.assertEqual(result.source, "rule:system_info")
        self.assertFalse(strategy.audit_records[0].accepted)
        self.assertIn("confidence", strategy.audit_records[0].fallback_reason)

    def test_output_validator_accepts_plain_json(self) -> None:
        proposal = LLMPlanOutputValidator().validate_raw_output(
            llm_output(valid_echo_payload())
        )

        self.assertEqual(proposal.suggested_action, "echo")
        self.assertEqual(proposal.arguments, {"text": "hola"})

    def test_output_validator_accepts_null_suggested_action_as_no_action(self) -> None:
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            proposal_provider=lambda llm_input, request: llm_output(
                {
                    "intent": "no registered tool fits",
                    "suggested_action": None,
                    "arguments": {},
                    "confidence": 0.2,
                }
            ),
        )

        result = Planner(strategy=strategy).create_plan(
            augmented_request("unmatched user goal")
        )

        self.assertEqual(result.status, "no_plan")
        self.assertEqual(result.source, "llm_assisted")
        self.assertFalse(result.metadata["fallback_used"])
        self.assertIsNone(result.metadata["proposal"]["suggested_action"])
        self.assertTrue(strategy.audit_records[0].accepted)

    def test_echo_tool_still_rejects_message_argument(self) -> None:
        with self.assertRaises(Exception):
            EchoTool().validate_input({"message": "hola"})

    def test_output_validator_accepts_json_fenced_block(self) -> None:
        proposal = LLMPlanOutputValidator().validate_raw_output(
            "```json\n" + llm_output(valid_echo_payload()) + "\n```"
        )

        self.assertEqual(proposal.suggested_action, "echo")
        self.assertEqual(proposal.arguments, {"text": "hola"})

    def test_output_validator_accepts_plain_fenced_block(self) -> None:
        proposal = LLMPlanOutputValidator().validate_raw_output(
            "```\n" + llm_output(valid_echo_payload()) + "\n```"
        )

        self.assertEqual(proposal.suggested_action, "echo")
        self.assertEqual(proposal.arguments, {"text": "hola"})

    def test_output_validator_rejects_text_mixed_with_json(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid JSON"):
            LLMPlanOutputValidator().validate_raw_output(
                "Here is the proposal:\n" + llm_output(valid_echo_payload())
            )

    def test_output_validator_rejects_unclosed_fenced_block(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid JSON"):
            LLMPlanOutputValidator().validate_raw_output(
                "```json\n" + llm_output(valid_echo_payload())
            )

    def test_fenced_valid_proposal_does_not_activate_fallback(self) -> None:
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            proposal_provider=lambda llm_input, request: (
                "```json\n" + llm_output(valid_echo_payload()) + "\n```"
            ),
        )

        result = Planner(strategy=strategy).create_plan(augmented_request("say hola"))

        self.assertEqual(result.source, "llm_assisted")
        self.assertFalse(result.metadata["fallback_used"])
        self.assertIsNone(result.metadata["fallback_reason"])
        self.assertTrue(strategy.audit_records[0].accepted)

    def test_llm_strategy_returns_valid_planned_action_when_output_is_valid(
        self,
    ) -> None:
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            proposal_provider=lambda llm_input, request: llm_output(valid_echo_payload()),
        )

        result = Planner(strategy=strategy).create_plan(augmented_request("say hola"))

        self.assertIsInstance(result, PlannedAction)
        self.assertEqual(result.source, "llm_assisted")
        self.assertEqual(result.tool_name, "echo")
        self.assertEqual(result.payload, {"text": "hola"})
        self.assertEqual(result.metadata["proposal"]["suggested_action"], "echo")
        self.assertTrue(strategy.audit_records[0].accepted)
        self.assertIsNone(strategy.audit_records[0].fallback_reason)

    def test_planner_strategy_does_not_execute_tool(self) -> None:
        tool = SpyEchoTool()
        registry = SpyRegistry(tool)
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            validator=LLMPlanOutputValidator(tool_registry=registry),
            proposal_provider=lambda llm_input, request: llm_output(
                {
                    "intent": "echo was requested",
                    "suggested_action": "echo",
                    "arguments": {"text": "hola"},
                    "confidence": 0.91,
                }
            ),
        )

        result = Planner(strategy=strategy).create_plan(
            augmented_request("say hola", dry_run=False)
        )

        self.assertEqual(result.source, "llm_assisted")
        self.assertEqual(tool.calls, 0)

    def test_planner_strategy_does_not_register_tool(self) -> None:
        registry = SpyRegistry(SpyEchoTool())
        strategy = LLMAssistedPlannerStrategy(
            enabled=True,
            validator=LLMPlanOutputValidator(tool_registry=registry),
            proposal_provider=lambda llm_input, request: llm_output(
                {
                    "intent": "echo was requested",
                    "suggested_action": "echo",
                    "arguments": {"text": "hola"},
                    "confidence": 0.91,
                }
            ),
        )

        Planner(strategy=strategy).create_plan(augmented_request("say hola"))

        self.assertEqual(registry.register_calls, 0)

    def test_runtime_still_calls_policy_after_planning(self) -> None:
        tool = SpyEchoTool()
        policy_engine = CountingPolicyEngine(PolicyDecisionValue.DENY)
        planner = Planner(
            strategy=LLMAssistedPlannerStrategy(
                enabled=True,
                proposal_provider=lambda llm_input, request: llm_output(
                    {
                        "intent": "echo was requested",
                        "suggested_action": "echo",
                        "arguments": {"text": "hola"},
                        "confidence": 0.91,
                    }
                ),
            )
        )
        runtime = AgentRuntime(
            runtime_planner=planner,
            runtime_policy_engine=policy_engine,
            tool_registry=SpyRegistry(tool),
            runtime_tracer=tracer(),
        )

        response = runtime.run(
            augmented_request("say hola", dry_run=False),
            context(),
        )

        self.assertEqual(response.status, ExecutionStatus.REJECTED)
        self.assertEqual(policy_engine.calls, 1)
        self.assertEqual(tool.calls, 0)


if __name__ == "__main__":
    unittest.main()
