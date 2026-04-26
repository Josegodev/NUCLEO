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

app = FastAPI(
    title="NUCLEO API",
    description="Runtime de agentes con control de políticas",
    version="0.1.0"
)

# Runtime Audit UI local-only CORS. This does not expose runtime decisions to
# the frontend; it only lets the browser read the existing HTTP API responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8766",
        "http://127.0.0.1:8767",
        "http://localhost:8766",
        "http://localhost:8767",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Idempotency-Key"],
)

app.include_router(health.router)
app.include_router(agent.router, prefix="/agent")
app.include_router(tools.router)
