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
from app.tools.registry import ToolRegistry
from app.tools.local.echo_tool import EchoTool
from app.tools.local.system_info_tool import SystemInfoTool
from app.policies.engine import PolicyEngine
from app.services.audit.audit_store import AuditStore
from app.services.staging.staging_registry import StagingRegistry
from app.services.tool_generation.tool_generation_service import ToolGenerationService
from app.services.tool_proposal.tool_proposal_service import ToolProposalService

registry = ToolRegistry()
registry.register(EchoTool())
registry.register(SystemInfoTool())

planner = Planner()
policy_engine = PolicyEngine()
audit_store = AuditStore()
proposal_service = ToolProposalService(audit_store=audit_store)
staging_registry = StagingRegistry(audit_store=audit_store)
tool_generation_service = ToolGenerationService(audit_store=audit_store)


class AgentRuntime:
    def run(self, request: AgentRequest, context: ExecutionContext) -> AgentResponse:
        plan = planner.create_plan(request)

        if plan.get("mode") == "capability_gap_detected":
            return self._handle_capability_gap(plan=plan, context=context)

        tool_name = plan["tool"]
        tool_payload = plan["payload"]

        policy_decision = policy_engine.evaluate(
            tool_name=tool_name,
            payload=tool_payload,
            dry_run=request.dry_run,
            context=context,
        )

        if policy_decision.decision == "deny":
            return AgentResponse(
                status="blocked",
                message=policy_decision.reason,
            )

        tool = registry.get(tool_name)
        if not tool:
            return AgentResponse(
                status="error",
                message=f"Planner requested unknown tool: {tool_name}",
            )

        result = tool.run(tool_payload, context=context)

        status = "dry_run_success" if request.dry_run else "success"

        return AgentResponse(
            status=status,
            message=str(result),
            result=result,
        )

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
