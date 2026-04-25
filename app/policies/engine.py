"""
NUCLEO - POLICY ENGINE

Componente responsable de validar si una acción propuesta por el planner
puede ser ejecutada.

Responsable de:
- Evaluar permisos de ejecución de tools
- Aplicar reglas de seguridad antes de la ejecución
- Considerar el contexto de ejecución autenticado
- Devolver decisiones estructuradas (PolicyDecision)

Flujo:
tool_name + payload + dry_run + context
    → evaluación de reglas
    → PolicyDecision (allow / deny)

Tipo de implementación:
- Whitelist estática (permitir solo tools explícitas)
- Estrategia "deny by default"
- Validación básica por usuario/rol

Salida:
PolicyDecision:
{
    decision: "allow" | "deny",
    reason: str
}

Notas:
- No ejecuta acciones, solo valida
- Se evalúa antes de acceder al registry o ejecutar tools
- Diseñado para ser extensible (reglas más complejas en el futuro)

Limitaciones actuales:
- No evalúa payload en profundidad
- No diferencia todavía reglas avanzadas entre dry_run y ejecución real
- Control de roles aún básico

Arquitectura:
Capa de control dentro del pipeline:
planner → policy → execution
"""

from app.policies.models import PolicyDecision
from app.schemas.context import ExecutionContext
from app.tools.registry import ToolRegistry
from app.tools.registry import registry as default_registry


class PolicyEngine:
    def __init__(self, tool_registry: ToolRegistry = default_registry) -> None:
        self._tool_registry = tool_registry

    def evaluate(
        self,
        tool_name: str,
        payload: dict,
        dry_run: bool,
        context: ExecutionContext,
    ) -> PolicyDecision:
        if not context.authenticated:
            return PolicyDecision(
                decision="deny",
                reason="unauthenticated request",
            )

        if self._tool_registry.get(tool_name) is None:
            return PolicyDecision(
                decision="deny",
                reason=f"tool '{tool_name}' is not allowed by policy",
            )

        if tool_name == "system_info" and "admin" not in context.roles:
            return PolicyDecision(
                decision="deny",
                reason=f"user '{context.username}' is not allowed to run 'system_info'",
            )

        return PolicyDecision(
            decision="allow",
            reason=f"{tool_name} tool is allowed for user '{context.username}'",
        )
