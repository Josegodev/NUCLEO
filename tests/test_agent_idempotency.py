import inspect
import unittest
from typing import get_args

from app.api.routes import agent as agent_route
from app.schemas.context import ExecutionContext
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse


class CountingAgentService:
    def __init__(self) -> None:
        self.calls = 0
        self.contexts = []

    def run(self, request, context) -> AgentResponse:
        self.calls += 1
        self.contexts.append(context)
        return AgentResponse(
            status="success",
            message=f"call-{self.calls}",
            result={
                "calls": self.calls,
                "dry_run": request.dry_run,
                "idempotency_key": context.idempotency_key,
            },
        )


def clear_idempotency_cache() -> None:
    with agent_route._IDEMPOTENCY_LOCK:
        agent_route._IDEMPOTENCY_CACHE.clear()


def context() -> ExecutionContext:
    return ExecutionContext(
        user_id="jose",
        username="jose",
        roles=["admin"],
        authenticated=True,
        request_id="idempotency-test",
        api_key_name="local_jose_dev",
    )


class AgentRunIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_agent_service = agent_route.agent_service
        clear_idempotency_cache()

    def tearDown(self) -> None:
        agent_route.agent_service = self.original_agent_service
        clear_idempotency_cache()

    def test_route_declares_x_idempotency_key_header(self) -> None:
        parameter = inspect.signature(agent_route.run_agent).parameters[
            "idempotency_key"
        ]
        header = get_args(parameter.annotation)[1]

        self.assertEqual(header.alias, "X-Idempotency-Key")

    def test_without_idempotency_key_runs_each_request_normally(self) -> None:
        service = CountingAgentService()
        agent_route.agent_service = service

        first_response = agent_route.run_agent(
            AgentRequest(user_input="system info", dry_run=True),
            context=context(),
        )
        second_response = agent_route.run_agent(
            AgentRequest(user_input="system info", dry_run=True),
            context=context(),
        )

        self.assertEqual(service.calls, 2)
        self.assertEqual(first_response.message, "call-1")
        self.assertEqual(second_response.message, "call-2")
        self.assertIsNone(service.contexts[0].idempotency_key)

    def test_with_idempotency_key_first_request_executes_once(self) -> None:
        service = CountingAgentService()
        agent_route.agent_service = service

        response = agent_route.run_agent(
            AgentRequest(user_input="system info", dry_run=True),
            context=context(),
            idempotency_key="retry-1",
        )

        self.assertEqual(service.calls, 1)
        self.assertEqual(service.contexts[0].idempotency_key, "retry-1")
        self.assertEqual(response.result["idempotency_key"], "retry-1")

    def test_second_request_with_same_idempotency_key_returns_cached_response(
        self,
    ) -> None:
        service = CountingAgentService()
        agent_route.agent_service = service

        first_response = agent_route.run_agent(
            AgentRequest(user_input="system info", dry_run=True),
            context=context(),
            idempotency_key="retry-2",
        )
        second_response = agent_route.run_agent(
            AgentRequest(user_input="system info", dry_run=True),
            context=context(),
            idempotency_key="retry-2",
        )

        self.assertEqual(service.calls, 1)
        self.assertEqual(first_response.model_dump(), second_response.model_dump())
        self.assertEqual(second_response.message, "call-1")

    def test_idempotency_preserves_dry_run_determinism(self) -> None:
        first_response = agent_route.run_agent(
            AgentRequest(user_input="system info", dry_run=True),
            context=context(),
            idempotency_key="dry-run-deterministic",
        )
        second_response = agent_route.run_agent(
            AgentRequest(user_input="system info", dry_run=True),
            context=context(),
            idempotency_key="dry-run-deterministic",
        )

        self.assertEqual(first_response.model_dump(), second_response.model_dump())
        self.assertEqual(first_response.status, "dry_run_success")
        self.assertEqual(first_response.result["executed"], False)
        self.assertEqual(first_response.result["tool"], "system_info")


if __name__ == "__main__":
    unittest.main()
