"""
NUCLEO - AGENT ROUTER

Endpoint principal para la ejecución de agentes.

Responsable de:
- Recibir solicitudes HTTP tipadas (AgentRequest)
- Resolver el contexto autenticado por request (ExecutionContext)
- Aplicar idempotencia HTTP opcional en el borde API
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

from threading import Lock
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps.auth import get_execution_context
from app.schemas.context import ExecutionContext
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.services.agent_service import AgentService

router = APIRouter()
agent_service = AgentService()
_IDEMPOTENCY_CACHE: dict[tuple[str, str | None, str], AgentResponse] = {}
_IDEMPOTENCY_LOCK = Lock()
_MAX_IDEMPOTENCY_KEY_LENGTH = 128


def _normalize_idempotency_key(idempotency_key: str | None) -> str | None:
    if idempotency_key is None:
        return None

    normalized_key = idempotency_key.strip()
    if not normalized_key:
        raise HTTPException(
            status_code=400,
            detail="X-Idempotency-Key must not be empty",
        )

    if len(normalized_key) > _MAX_IDEMPOTENCY_KEY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=(
                "X-Idempotency-Key must be "
                f"{_MAX_IDEMPOTENCY_KEY_LENGTH} characters or fewer"
            ),
        )

    return normalized_key


@router.post("/run", response_model=AgentResponse)
def run_agent(
    request: AgentRequest,
    context: ExecutionContext = Depends(get_execution_context),
    idempotency_key: Annotated[str | None, Header(alias="X-Idempotency-Key")] = None,
):
    normalized_key = _normalize_idempotency_key(idempotency_key)
    if normalized_key is None:
        return agent_service.run(request, context)

    cache_key = (context.user_id, context.api_key_name, normalized_key)
    idempotent_context = context.model_copy(
        update={"idempotency_key": normalized_key}
    )

    with _IDEMPOTENCY_LOCK:
        cached_response = _IDEMPOTENCY_CACHE.get(cache_key)
        if cached_response is not None:
            return cached_response.model_copy(deep=True)

        response = agent_service.run(request, idempotent_context)
        _IDEMPOTENCY_CACHE[cache_key] = response.model_copy(deep=True)
        return response
