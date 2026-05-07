"""
NUCLEO - API ENTRYPOINT

FastAPI application bootstrap.
Responsable de:
- Inicializar la app
- Registrar routers
- Exponer endpoints HTTP

Flujo:
HTTP → routes → runtime → policies → tools
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, agent, tools
from app.core.config import (
    LOCAL_UI_CORS_HEADERS,
    LOCAL_UI_CORS_METHODS,
    LOCAL_UI_CORS_ORIGINS,
)

app = FastAPI(
    title="NUCLEO API",
    description="Runtime de agentes con control de políticas",
    version="0.1.0"
)

# Local browser UIs CORS. This does not expose runtime decisions to the
# frontend; it only lets the browser read existing HTTP API responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_UI_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=LOCAL_UI_CORS_METHODS,
    allow_headers=LOCAL_UI_CORS_HEADERS,
)

app.include_router(health.router)
app.include_router(agent.router, prefix="/agent")
app.include_router(tools.router)
