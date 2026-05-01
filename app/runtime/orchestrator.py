"""
NUCLEO - AGENT RUNTIME (ORCHESTRATOR)

Motor central de ejecución de agentes.

Responsable de:
- Transformar una solicitud (AgentRequest) en un plan ejecutable
- Validar la ejecución mediante políticas (PolicyEngine)
- Resolver la herramienta adecuada (ToolRegistry)
- Ejecutar la acción correspondiente (Tool)
- Propagar el ExecutionContext a policy y tools
- Devolver una respuesta estructurada (AgentResponse)

Flujo:
AgentRequest
    → Planner (create_plan)
    → PolicyEngine (evaluate)
    → ToolRegistry (get tool)
    → Tool (run)
    → AgentResponse

Componentes:
- Planner: propone una acción candidata determinista
- ToolRegistry: mantiene catálogo de herramientas ejecutables
- PolicyEngine: controla permisos y seguridad
- Tools: implementaciones concretas de ejecución

Notas:
- Soporta modo 'dry_run' para simulación sin ejecución real
- Todas las acciones pasan por validación de políticas
- Diseñado para ser extensible (nuevas tools, nuevas policies)

Arquitectura:
Command Execution Pipeline con control de políticas.
"""

from pydantic import ValidationError

from app.schemas.context import ExecutionContext
from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentRequest
from app.schemas.responses import (
    AgentResponse,
    ExecutionError,
    ExecutionErrorCode,
    ExecutionStatus,
)
from app.runtime.planner import Planner
from app.runtime.planner_augmentation import (
    LLMAssistedPlannerStrategy,
    ModelRouterProposalProvider,
)
from app.runtime.tracing import ExecutionStep, ExecutionTrace, InMemoryTracer, Tracer
from app.tools.registry import registry
from app.policies.engine import PolicyEngine
from app.policies.models import PolicyDecision, PolicyDecisionValue

planner = Planner(
    strategy=LLMAssistedPlannerStrategy(
        enabled=True,
        proposal_provider=ModelRouterProposalProvider(),
    )
)
policy_engine = PolicyEngine(tool_registry=registry)
tracer = InMemoryTracer()


class AgentRuntime:
    def __init__(
        self,
        runtime_planner: Planner | None = None,
        runtime_policy_engine: PolicyEngine | None = None,
        tool_registry=registry,
        runtime_tracer: Tracer | None = None,
    ) -> None:
        self._planner = runtime_planner or planner
        self._policy_engine = runtime_policy_engine or policy_engine
        self._registry = tool_registry
        self._tracer = runtime_tracer or tracer

    def run(self, request: AgentRequest, context: ExecutionContext) -> AgentResponse:
        trace = self._safe_start_trace(context.request_id)
        trace_id = trace.trace_id
        try:
            plan = self._planner.create_plan(request)
            self._validate_planner_result(plan)
        except ValidationError as exc:
            self._safe_record_step(
                trace=trace,
                phase="planner",
                input={"user_input": request.user_input},
                output={},
                status="error",
                error=str(exc),
            )
            return self._error_response(
                status=ExecutionStatus.REJECTED,
                code=ExecutionErrorCode.TOOL_INPUT_INVALID,
                message=f"Planner rejected invalid action input: {exc}",
                trace_id=trace_id,
            )
        except Exception as exc:
            self._safe_record_step(
                trace=trace,
                phase="planner",
                input={"user_input": request.user_input},
                output={},
                status="error",
                error=str(exc),
            )
            return self._error_response(
                status=ExecutionStatus.ERROR,
                code=ExecutionErrorCode.PLANNER_INVALID_RESULT,
                message=f"Planner failed to produce a valid result: {exc}",
                trace_id=trace_id,
            )

        self._safe_record_step(
            trace=trace,
            phase="planner",
            input={"user_input": request.user_input},
            output=plan.model_dump(mode="json"),
            status="success",
        )

        if plan.status == "no_plan":
            return self._error_response(
                status=ExecutionStatus.REJECTED,
                code=ExecutionErrorCode.NO_PLAN,
                message=plan.reason,
                trace_id=trace_id,
            )

        tool_name = plan.tool_name
        tool_payload = plan.payload

        try:
            policy_decision = self._policy_engine.evaluate(
                tool_name=tool_name,
                payload=tool_payload,
                dry_run=request.dry_run,
                context=context,
            )
            self._validate_policy_result(policy_decision)
        except Exception as exc:
            self._safe_record_step(
                trace=trace,
                phase="policy",
                input={
                    "tool": tool_name,
                    "payload": tool_payload,
                    "dry_run": request.dry_run,
                },
                output={},
                status="error",
                error=str(exc),
            )
            return self._error_response(
                status=ExecutionStatus.ERROR,
                code=ExecutionErrorCode.POLICY_INVALID_RESULT,
                message=f"PolicyEngine failed to produce a valid result: {exc}",
                trace_id=trace_id,
            )

        self._safe_record_step(
            trace=trace,
            phase="policy",
            input={
                "tool": tool_name,
                "payload": tool_payload,
                "dry_run": request.dry_run,
                "context": {
                    "request_id": context.request_id,
                    "username": context.username,
                    "roles": context.roles,
                    "authenticated": context.authenticated,
                },
            },
            output=policy_decision.model_dump(mode="json"),
            status=(
                "denied"
                if policy_decision.decision == PolicyDecisionValue.DENY
                else "success"
            ),
            error=(
                policy_decision.reason
                if policy_decision.decision == PolicyDecisionValue.DENY
                else None
            ),
        )

        if policy_decision.decision == PolicyDecisionValue.DENY:
            return self._error_response(
                status=ExecutionStatus.REJECTED,
                code=ExecutionErrorCode.POLICY_DENIED,
                message=policy_decision.reason,
                trace_id=trace_id,
            )

        tool = self._registry.get(tool_name)
        self._safe_record_step(
            trace=trace,
            phase="registry",
            input={"tool": tool_name},
            output={
                "found": tool is not None,
                "tool": getattr(tool, "name", None),
            },
            status="success" if tool else "error",
            error=None if tool else f"Planner proposed unknown tool: {tool_name}",
        )
        if not tool:
            return self._error_response(
                status=ExecutionStatus.ERROR,
                code=ExecutionErrorCode.TOOL_NOT_FOUND,
                message=f"Planner proposed unknown tool: {tool_name}",
                trace_id=trace_id,
            )

        try:
            tool_payload = tool.validate_input(tool_payload)
        except Exception as exc:
            self._safe_record_step(
                trace=trace,
                phase="tool",
                input={
                    "tool": tool_name,
                    "payload": plan.payload,
                    "dry_run": request.dry_run,
                },
                output={},
                status="error",
                error=str(exc),
            )
            return self._error_response(
                status=ExecutionStatus.REJECTED,
                code=ExecutionErrorCode.TOOL_INPUT_INVALID,
                message=f"Tool input does not match contract: {exc}",
                trace_id=trace_id,
            )

        if request.dry_run:
            result = {
                "dry_run": True,
                "executed": False,
                "tool": tool_name,
                "payload": tool_payload,
            }
            result.update(plan.metadata)
            self._safe_record_step(
                trace=trace,
                phase="tool",
                input={"tool": tool_name, "payload": tool_payload, "dry_run": True},
                output={**result, "reason": "dry_run"},
                status="skipped",
            )
            return AgentResponse(
                status=ExecutionStatus.SUCCESS,
                result=result,
                trace_id=trace_id,
            )

        try:
            raw_result = tool.run(tool_payload, context=context)
        except Exception as exc:
            self._safe_record_step(
                trace=trace,
                phase="tool",
                input={"tool": tool_name, "payload": tool_payload, "dry_run": False},
                output={},
                status="error",
                error=str(exc),
            )
            return self._error_response(
                status=ExecutionStatus.ERROR,
                code=ExecutionErrorCode.TOOL_EXECUTION_FAILED,
                message=f"Tool execution failed: {exc}",
                trace_id=trace_id,
            )

        try:
            result = tool.validate_output(raw_result)
        except Exception as exc:
            self._safe_record_step(
                trace=trace,
                phase="tool",
                input={"tool": tool_name, "payload": tool_payload, "dry_run": False},
                output=raw_result if isinstance(raw_result, dict) else {},
                status="error",
                error=str(exc),
            )
            return self._error_response(
                status=ExecutionStatus.ERROR,
                code=ExecutionErrorCode.TOOL_OUTPUT_INVALID,
                message=f"Tool output does not match contract: {exc}",
                trace_id=trace_id,
            )

        self._safe_record_step(
            trace=trace,
            phase="tool",
            input={"tool": tool_name, "payload": tool_payload, "dry_run": False},
            output=result,
            status="success",
        )

        if result.get("status") == "error":
            return self._error_response(
                status=ExecutionStatus.ERROR,
                code=ExecutionErrorCode.TOOL_REPORTED_ERROR,
                message=str(result.get("message", "tool reported error")),
                trace_id=trace_id,
                result=result,
            )

        return AgentResponse(
            status=ExecutionStatus.SUCCESS,
            result=result,
            trace_id=trace_id,
        )

    def _validate_planner_result(self, plan: PlannedAction) -> None:
        if not isinstance(plan, PlannedAction):
            raise TypeError("Planner must return PlannedAction")

    def _validate_policy_result(self, decision: PolicyDecision) -> None:
        if not isinstance(decision, PolicyDecision):
            raise TypeError("PolicyEngine must return PolicyDecision")

    def _error_response(
        self,
        status: ExecutionStatus,
        code: ExecutionErrorCode,
        message: str,
        trace_id: str,
        result: dict | None = None,
    ) -> AgentResponse:
        return AgentResponse(
            status=status,
            result=result,
            errors=[ExecutionError(code=code, message=message)],
            trace_id=trace_id,
        )

    def _safe_start_trace(self, request_id: str | None) -> ExecutionTrace:
        try:
            return self._tracer.start_trace(request_id=request_id)
        except Exception:
            return ExecutionTrace(
                trace_id=f"trace-{request_id or 'unavailable'}",
                request_id=request_id,
            )

    def _safe_record_step(
        self,
        trace: ExecutionTrace | None,
        phase: str,
        input: dict,
        output: dict,
        status: str,
        error: str | None = None,
    ) -> None:
        if trace is None:
            return

        try:
            step = ExecutionStep(
                step_id="",
                phase=phase,
                input=input,
                output=output,
                status=status,
                error=error,
                timestamp="",
            )
            self._tracer.record_step(
                trace=trace,
                step=step,
            )
        except Exception:
            return
