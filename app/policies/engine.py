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
    → PolicyDecision (PolicyDecisionValue.ALLOW / PolicyDecisionValue.DENY)

Tipo de implementación:
- Whitelist estática (permitir solo tools explícitas)
- Estrategia "deny by default"
- Validación básica por usuario/rol

Salida:
PolicyDecision:
{
    decision: PolicyDecisionValue,
    reason: str
    validated_fields: list[PolicyValidatedField]
}

Notas:
- No ejecuta acciones, solo valida
- Runtime resuelve la instancia de tool después de PolicyDecisionValue.ALLOW
- Diseñado para ser extensible (reglas más complejas en el futuro)

Limitaciones actuales:
- No diferencia todavía reglas avanzadas entre dry_run y ejecución real
- Control de roles aún básico

Contrato actual:
- Valida el payload contra el contrato de la tool antes de devolver ALLOW
- No ejecuta acciones; la ejecución sigue perteneciendo al runtime

Arquitectura:
Capa de control dentro del pipeline:
planner → policy → registry → execution
"""

from pydantic import ValidationError

from app.policies.models import PolicyDecision, PolicyDecisionValue, PolicyValidatedField
from app.schemas.context import ExecutionContext
from app.schemas.artifacts import KNOWN_TOOL_NAMES, validate_tool_payload
from app.tools.registry import ToolRegistry
from app.tools.registry import registry as default_registry


class PolicyEngine:
    ALLOWED_TOOL_NAMES = set(KNOWN_TOOL_NAMES)

    def __init__(self, tool_registry: ToolRegistry = default_registry) -> None:
        self._tool_registry = tool_registry

    def evaluate(
        self,
        tool_name: str,
        payload: dict,
        dry_run: bool,
        context: ExecutionContext,
    ) -> PolicyDecision:
        validated_fields: list[PolicyValidatedField] = [
            PolicyValidatedField.AUTHENTICATED_CONTEXT
        ]

        if not context.authenticated:
            return PolicyDecision(
                decision=PolicyDecisionValue.DENY,
                reason="unauthenticated request",
                validated_fields=validated_fields,
            )

        validated_fields.append(PolicyValidatedField.TOOL_NAME)
        if tool_name not in self.ALLOWED_TOOL_NAMES:
            return PolicyDecision(
                decision=PolicyDecisionValue.DENY,
                reason=f"tool '{tool_name}' is not allowed by policy",
                validated_fields=validated_fields,
            )

        validated_fields.append(PolicyValidatedField.TOOL_REGISTERED)
        if self._tool_registry.get(tool_name) is None:
            return PolicyDecision(
                decision=PolicyDecisionValue.DENY,
                reason=f"tool '{tool_name}' is not registered",
                validated_fields=validated_fields,
            )

        validated_fields.append(PolicyValidatedField.DRY_RUN)
        if not isinstance(dry_run, bool):
            return PolicyDecision(
                decision=PolicyDecisionValue.DENY,
                reason="dry_run must be a boolean",
                validated_fields=validated_fields,
            )

        validated_fields.append(PolicyValidatedField.PAYLOAD)
        try:
            validate_tool_payload(tool_name, payload)
        except (TypeError, ValueError, ValidationError) as exc:
            return PolicyDecision(
                decision=PolicyDecisionValue.DENY,
                reason=f"payload does not match tool contract: {exc}",
                validated_fields=validated_fields,
            )

        validated_fields.append(PolicyValidatedField.ROLE)
        if tool_name == "system_info" and "admin" not in context.roles:
            return PolicyDecision(
                decision=PolicyDecisionValue.DENY,
                reason=f"user '{context.username}' is not allowed to run 'system_info'",
                validated_fields=validated_fields,
            )

        return PolicyDecision(
            decision=PolicyDecisionValue.ALLOW,
            reason=f"{tool_name} tool is allowed for user '{context.username}'",
            validated_fields=validated_fields,
        )
