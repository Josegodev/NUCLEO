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
from app.api.routes import health, agent, tools

app = FastAPI(
    title="NUCLEO API",
    description="Runtime de agentes con control de políticas",
    version="0.1.0"
)

app.include_router(health.router)
app.include_router(agent.router, prefix="/agent")
app.include_router(tools.router)