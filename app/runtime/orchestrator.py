"""
NUCLEO - AGENT RUNTIME (ORCHESTRATOR)

Motor central de ejecución de agentes.

Responsable de:
- Transformar una solicitud (AgentRequest) en un plan ejecutable
- Validar la ejecución mediante políticas (PolicyEngine)
- Resolver la herramienta adecuada (ToolRegistry)
- Ejecutar la acción correspondiente (Tool)
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

from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.runtime.planner import Planner
from app.tools.registry import ToolRegistry
from app.tools.local.echo_tool import EchoTool
from app.tools.local.system_info_tool import SystemInfoTool
from app.policies.engine import PolicyEngine

registry = ToolRegistry()
registry.register(EchoTool())
registry.register(SystemInfoTool())

planner = Planner()
policy_engine = PolicyEngine()


class AgentRuntime:
    def run(self, request: AgentRequest) -> AgentResponse:
        plan = planner.create_plan(request)

        tool_name = plan["tool"]
        tool_payload = plan["payload"]

        policy_decision = policy_engine.evaluate(
            tool_name=tool_name,
            payload=tool_payload,
            dry_run=request.dry_run,
        )

        if policy_decision.decision == "deny":
            return AgentResponse(
                status="blocked",
                message=policy_decision.reason
            )

        tool = registry.get(tool_name)
        if not tool:
            return AgentResponse(
                status="error",
                message=f"Planner requested unknown tool: {tool_name}"
            )

        result = tool.run(tool_payload)

        status = "dry_run_success" if request.dry_run else "success"

        return AgentResponse(
            status=status,
            message=str(result)
        )