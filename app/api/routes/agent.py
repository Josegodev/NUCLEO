"""
NUCLEO - AGENT ROUTER

Endpoint principal para la ejecución de agentes.

Responsable de:
- Recibir solicitudes HTTP tipadas (AgentRequest)
- Delegar la ejecución al runtime (AgentRuntime)
- Devolver respuestas estructuradas (AgentResponse)

Flujo:
HTTP → AgentRequest → runtime.run() → AgentResponse → HTTP

Notas:
- No contiene lógica de negocio
- Actúa como capa de interfaz (API)
- Toda la ejecución se realiza en el runtime
"""

from fastapi import APIRouter
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.runtime.orchestrator import AgentRuntime

router = APIRouter()
runtime = AgentRuntime()

@router.post("/run", response_model=AgentResponse)
def run_agent(request: AgentRequest):
    return runtime.run(request)