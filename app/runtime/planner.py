"""
NUCLEO - PLANNER

Componente responsable de transformar una solicitud de usuario
(AgentRequest) en un plan de ejecución estructurado.

Responsable de:
- Interpretar la entrada del usuario de forma determinista
- Proponer una acción estructurada candidata
- Construir el payload necesario para dicha herramienta

Flujo:
AgentRequest → normalización → tabla de reglas → PlannedAction

Tipo de implementación:
- Rule-based (determinista)
- Basado en una tabla explícita de reglas auditables

Salida:
PlannedAction con estructura estable:
{
    "tool_name": str | None,
    "payload": dict,
    "confidence": float,
    "reason": str,
    "status": "planned" | "no_plan"
}

Notas:
- No ejecuta lógica ni valida permisos
- No interactúa con tools directamente
- No inventa tools: solo planifica tools presentes en ToolRegistry
- Su salida es consumida por el runtime (orchestrator)

Limitaciones actuales:
- Matching simple mediante reglas explícitas
- No soporta múltiples acciones ni composición de tools
- No utiliza contexto ni memoria

	Arquitectura:
	Componente de decisión dentro del pipeline:
	input → planner → policy → registry → execution
"""

from dataclasses import dataclass
from typing import Callable

from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentRequest
from app.tools.registry import ToolRegistry
from app.tools.registry import registry as default_registry


PayloadBuilder = Callable[[AgentRequest], dict]
Matcher = Callable[[str, AgentRequest], bool]


@dataclass(frozen=True)
class PlannerRule:
    name: str
    tool_name: str
    matches: Matcher
    build_payload: PayloadBuilder
    confidence: float
    reason: str


class Planner:
    def __init__(
        self,
        tool_registry: ToolRegistry = default_registry,
        rules: list[PlannerRule] | None = None,
    ) -> None:
        self._tool_registry = tool_registry
        self._rules = rules or self._default_rules()

    def create_plan(self, request: AgentRequest) -> PlannedAction:
        structured_payload = request.payload or {}
        raw_input = request.user_input or ""
        normalized_input = raw_input.strip().lower()

        if request.tool:
            if not self._tool_exists(request.tool):
                return PlannedAction(
                    payload=structured_payload,
                    status="no_plan",
                    confidence=0.0,
                    reason=f"Explicit tool is not registered: {request.tool}",
                    source="explicit_request",
                )

            return PlannedAction(
                tool_name=request.tool,
                payload=structured_payload,
                status="planned",
                confidence=1.0,
                reason="Explicit tool requested by caller.",
                source="explicit_request",
            )

        for rule in self._rules:
            if not rule.matches(normalized_input, request):
                continue

            if not self._tool_exists(rule.tool_name):
                return PlannedAction(
                    payload=structured_payload,
                    status="no_plan",
                    confidence=0.0,
                    reason=f"Matched rule '{rule.name}', but tool is not registered: {rule.tool_name}",
                    source=f"rule:{rule.name}",
                )

            return PlannedAction(
                tool_name=rule.tool_name,
                payload=rule.build_payload(request),
                status="planned",
                confidence=rule.confidence,
                reason=rule.reason,
                source=f"rule:{rule.name}",
            )

        return PlannedAction(
            payload=structured_payload,
            status="no_plan",
            confidence=0.0,
            reason="No deterministic planner rule matched the request.",
            source="rule_table",
        )

    def _tool_exists(self, tool_name: str) -> bool:
        return self._tool_registry.get(tool_name) is not None

    def _default_rules(self) -> list[PlannerRule]:
        return [
            PlannerRule(
                name="disk_info",
                tool_name="disk_info",
                matches=lambda normalized_input, request: "disk info" in normalized_input
                or "disk" in normalized_input,
                build_payload=self._build_disk_payload,
                confidence=0.9,
                reason="Request matched deterministic disk information rule.",
            ),
            PlannerRule(
                name="system_info",
                tool_name="system_info",
                matches=lambda normalized_input, request: "system" in normalized_input
                or "info" in normalized_input,
                build_payload=lambda request: request.payload or {},
                confidence=0.85,
                reason="Request matched deterministic system information rule.",
            ),
        ]

    @staticmethod
    def _build_disk_payload(request: AgentRequest) -> dict:
        structured_payload = request.payload or {}
        disk_path_from_text = Planner._extract_path_from_text(request.user_input or "")
        return Planner._merge_disk_payload(structured_payload, disk_path_from_text)

    @staticmethod
    def _extract_path_from_text(user_input: str) -> str | None:
        marker = "path="
        lower_input = user_input.lower()
        marker_index = lower_input.find(marker)
        if marker_index == -1:
            return None

        path_value = user_input[marker_index + len(marker):].strip()
        if not path_value:
            return None

        for separator in (" ", ",", ";"):
            separator_index = path_value.find(separator)
            if separator_index != -1:
                path_value = path_value[:separator_index]
                break

        return path_value.strip() or None

    @staticmethod
    def _merge_disk_payload(payload: dict, path_from_text: str | None) -> dict:
        merged_payload = dict(payload)
        if "path" not in merged_payload and path_from_text:
            merged_payload["path"] = path_from_text
        return merged_payload
