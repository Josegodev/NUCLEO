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
        structured_payload = request.payload or {}
        raw_input = request.user_input or ""
        normalized_input = raw_input.strip().lower()

        if request.tool:
            return {
                "tool": request.tool,
                "payload": structured_payload,
            }

        disk_path_from_text = self._extract_path_from_text(raw_input)
        disk_payload = self._merge_disk_payload(structured_payload, disk_path_from_text)

        if self._is_disk_info_request(normalized_input):
            return {
                "tool": "disk_info",
                "payload": disk_payload,
                "mode": "existing_tool",
            }

        if "system" in normalized_input or "info" in normalized_input:
            return {
                "tool": "system_info",
                "payload": structured_payload,
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
                "payload": structured_payload,
                "mode": gap.type,
                "original_input": raw_input,
                "capability_gap": gap.dict(),
            }

        return {
            "tool": "echo",
            "payload": {
                "text": raw_input
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

    @staticmethod
    def _is_disk_info_request(normalized_input: str) -> bool:
        return "disk info" in normalized_input or "disk" in normalized_input

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
