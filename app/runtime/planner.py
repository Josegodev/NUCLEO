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


class Planner:
    def create_plan(self, request: AgentRequest) -> dict:
        normalized_input = request.user_input.strip().lower()

        if "system" in normalized_input or "info" in normalized_input:
            return {
                "tool": "system_info",
                "payload": {}
            }

        return {
            "tool": "echo",
            "payload": {
                "text": request.user_input
            }
        }