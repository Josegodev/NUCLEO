"""
NUCLEO - POLICY ENGINE

Componente responsable de validar si una acción propuesta por el planner
puede ser ejecutada.

Responsable de:
- Evaluar permisos de ejecución de tools
- Aplicar reglas de seguridad antes de la ejecución
- Devolver decisiones estructuradas (PolicyDecision)

Flujo:
tool_name + payload + dry_run
    → evaluación de reglas
    → PolicyDecision (allow / deny)

Tipo de implementación:
- Whitelist estática (permitir solo tools explícitas)
- Estrategia "deny by default"

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
- No evalúa payload
- No diferencia entre dry_run y ejecución real
- No considera contexto (usuario, entorno, estado)

Arquitectura:
Capa de control dentro del pipeline:
planner → policy → execution
"""

from app.policies.models import PolicyDecision


class PolicyEngine:
    def evaluate(self, tool_name: str, payload: dict, dry_run: bool) -> PolicyDecision:
        if tool_name in {"echo", "system_info"}:
            return PolicyDecision(
                decision="allow",
                reason=f"{tool_name} tool is allowed"
            )

        return PolicyDecision(
            decision="deny",
            reason=f"tool '{tool_name}' is not allowed by policy"
        )