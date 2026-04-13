"""
NUCLEO - AGENT ROUTER

Endpoint principal para la ejecución de agentes.

Responsable de:
- Recibir solicitudes HTTP tipadas (AgentRequest)
- Resolver el contexto autenticado por request (ExecutionContext)
- Delegar la ejecución al service (AgentService)
- Devolver respuestas estructuradas (AgentResponse)

Flujo:
HTTP
    → Auth dependency (API key)
    → ExecutionContext
    → AgentRequest
    → AgentService
    → runtime.run()
    → AgentResponse
    → HTTP

Notas:
- No contiene lógica de negocio
- No valida credenciales directamente
- Actúa como capa de interfaz (API)
- Toda la ejecución se realiza en capas inferiores
"""

from fastapi import APIRouter, Depends

from app.api.deps.auth import get_execution_context
from app.schemas.context import ExecutionContext
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.services.agent_service import AgentService

router = APIRouter()
agent_service = AgentService()


@router.post("/run", response_model=AgentResponse)
def run_agent(
    request: AgentRequest,
    context: ExecutionContext = Depends(get_execution_context),
):
    return agent_service.run(request, context)