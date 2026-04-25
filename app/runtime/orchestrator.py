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
- Planner: decide qué acción ejecutar
- PolicyEngine: controla permisos y seguridad
- ToolRegistry: mantiene catálogo de herramientas
- Tools: implementaciones concretas de ejecución

Notas:
- Soporta modo 'dry_run' para simulación sin ejecución real
- Todas las acciones pasan por validación de políticas
- Diseñado para ser extensible (nuevas tools, nuevas policies)

Arquitectura:
Command Execution Pipeline con control de políticas.
"""

from app.schemas.context import ExecutionContext
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.runtime.planner import Planner
from app.runtime.tracing import ExecutionStep, ExecutionTrace, InMemoryTracer, Tracer
from app.tools.registry import registry
from app.policies.engine import PolicyEngine
from app.services.audit.audit_store import AuditStore
from app.services.staging.staging_registry import StagingRegistry
from app.services.tool_generation.tool_generation_service import ToolGenerationService
from app.services.tool_proposal.tool_proposal_service import ToolProposalService

planner = Planner()
policy_engine = PolicyEngine(tool_registry=registry)
audit_store = AuditStore()
proposal_service = ToolProposalService(audit_store=audit_store)
staging_registry = StagingRegistry(audit_store=audit_store)
tool_generation_service = ToolGenerationService(audit_store=audit_store)
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
        plan = self._planner.create_plan(request)
        self._safe_record_step(
            trace=trace,
            phase="planner",
            input={"user_input": request.user_input},
            output=plan,
            status="success",
        )

        if plan.get("mode") == "capability_gap_detected":
            return self._handle_capability_gap(plan=plan, context=context)

        tool_name = plan["tool"]
        tool_payload = plan["payload"]

        policy_decision = self._policy_engine.evaluate(
            tool_name=tool_name,
            payload=tool_payload,
            dry_run=request.dry_run,
            context=context,
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
            output=policy_decision.model_dump(),
            status="denied" if policy_decision.decision == "deny" else "success",
            error=policy_decision.reason if policy_decision.decision == "deny" else None,
        )

        if policy_decision.decision == "deny":
            return AgentResponse(
                status="blocked",
                message=policy_decision.reason,
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
            error=None if tool else f"Planner requested unknown tool: {tool_name}",
        )
        if not tool:
            message = f"Planner requested unknown tool: {tool_name}"
            return AgentResponse(
                status="error",
                message=message,
            )

        if request.dry_run:
            result = {
                "dry_run": True,
                "executed": False,
                "tool": tool_name,
                "payload": tool_payload,
            }
            self._safe_record_step(
                trace=trace,
                phase="tool",
                input={"tool": tool_name, "payload": tool_payload, "dry_run": True},
                output={**result, "reason": "dry_run"},
                status="skipped",
            )
            return AgentResponse(
                status="dry_run_success",
                message=str(result),
                result=result,
            )

        try:
            result = tool.run(tool_payload, context=context)
        except Exception as exc:
            self._safe_record_step(
                trace=trace,
                phase="tool",
                input={"tool": tool_name, "payload": tool_payload, "dry_run": False},
                output={},
                status="error",
                error=str(exc),
            )
            raise

        self._safe_record_step(
            trace=trace,
            phase="tool",
            input={"tool": tool_name, "payload": tool_payload, "dry_run": False},
            output=result,
            status="success",
        )

        return AgentResponse(
            status="success",
            message=str(result),
            result=result,
        )

    def _safe_start_trace(self, request_id: str | None) -> ExecutionTrace | None:
        try:
            return self._tracer.start_trace(request_id=request_id)
        except Exception:
            return None

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

    def _handle_capability_gap(
        self,
        plan: dict,
        context: ExecutionContext,
    ) -> AgentResponse:
        gap = plan["capability_gap"]
        proposal = proposal_service.create_from_gap(
            user_input=plan.get("original_input", gap["capability_name"]),
            capability_name=gap["capability_name"],
            context=context,
        )
        proposal_path = f"runtime_lab/proposals/{proposal.proposal_id}.json"
        staging_registry.register_proposal(proposal, proposal_path=proposal_path)
        generated_artifacts = tool_generation_service.generate_from_proposal(proposal)
        staging_registry.update_status(
            proposal_id=proposal.proposal_id,
            status="generated",
            generated_path=generated_artifacts["tool_dir"],
        )
        audit_store.record(
            event="capability_gap_handled",
            proposal_id=proposal.proposal_id,
            action="planner_gap_to_staging",
            result="success",
            artifact_paths=[proposal_path, generated_artifacts["tool_dir"]],
            metadata={
                "capability_name": gap["capability_name"],
                "requested_by": context.username,
            },
        )
        return AgentResponse(
            status="capability_gap",
            message=gap["reason"],
            result={
                "capability_gap_detected": True,
                "proposal_id": proposal.proposal_id,
                "proposal_path": proposal_path,
                "generated_artifacts": generated_artifacts,
                "staging_status": "generated",
                "production_registry_unchanged": True,
            },
        )
