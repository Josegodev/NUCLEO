"""
NUCLEO - PLANNER

Componente responsable de transformar una solicitud de usuario
(AgentRequest) en un plan de ejecución estructurado.

Responsable de:
- Interpretar la entrada del usuario
- Determinar qué herramienta (tool) debe ejecutarse
- Construir el payload necesario para dicha herramienta

Flujo:
AgentRequest → normalización → reglas → plan (tool + payload)

Tipo de implementación:
- Rule-based (determinista)
- Basado en coincidencia de palabras clave

Salida:
dict con estructura:
{
    "tool": str,
    "payload": dict
}

Notas:
- No ejecuta lógica ni valida permisos
- No interactúa con tools directamente
- Su salida es consumida por el runtime (orchestrator)

Limitaciones actuales:
- Matching simple por palabras clave
- No soporta múltiples acciones ni composición de tools
- No utiliza contexto ni memoria

Arquitectura:
Componente de decisión dentro del pipeline:
input → planner → policy → execution
"""

from app.schemas.requests import AgentRequest
from app.schemas.tool_proposal import CapabilityGapSignal


class Planner:
    def create_plan(self, request: AgentRequest) -> dict:
        normalized_input = request.user_input.strip().lower()

        if "system" in normalized_input or "info" in normalized_input:
            return {
                "tool": "system_info",
                "payload": {},
                "mode": "existing_tool",
            }

        if request.experimental_tool_generation and self._looks_like_capability_gap(
            normalized_input
        ):
            gap = CapabilityGapSignal(
                capability_name=self._infer_capability_name(normalized_input),
                reason=(
                    "Planner did not find a production tool for the requested capability."
                ),
                proposal_generation_requested=True,
            )
            return {
                "tool": None,
                "payload": {},
                "mode": gap.type,
                "original_input": request.user_input,
                "capability_gap": gap.dict(),
            }

        return {
            "tool": "echo",
            "payload": {
                "text": request.user_input
            },
            "mode": "existing_tool",
        }

    @staticmethod
    def _looks_like_capability_gap(normalized_input: str) -> bool:
        hint_tokens = {
            "create",
            "build",
            "fetch",
            "search",
            "query",
            "calculate",
            "generate",
            "integrate",
        }
        return any(token in normalized_input for token in hint_tokens)

    @staticmethod
    def _infer_capability_name(normalized_input: str) -> str:
        words = [word for word in normalized_input.split() if word.isascii()]
        if not words:
            return "unclassified_capability"
        return "_".join(words[:4])
