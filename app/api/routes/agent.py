"""
NUCLEO - AGENT ROUTER

Endpoint principal para la ejecución de agentes.

Responsable de:
- Recibir solicitudes HTTP tipadas (AgentRequest)
- Delegar la ejecución al service (AgentService)
- Devolver respuestas estructuradas (AgentResponse)

Flujo:
HTTP → AgentRequest → AgentService → runtime.run() → AgentResponse → HTTP

Notas:
- No contiene lógica de negocio
- Actúa como capa de interfaz (API)
- Toda la ejecución se realiza en capas inferiores
"""

from fastapi import APIRouter
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.services.agent_service import AgentService

router = APIRouter()
agent_service = AgentService()

@router.post("/run", response_model=AgentResponse)
def run_agent(request: AgentRequest):
    return agent_service.run(request)