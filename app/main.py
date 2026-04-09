from fastapi import FastAPI

from app.api.routes import health, agent, tools

app = FastAPI()

app.include_router(health.router)
app.include_router(agent.router, prefix="/agent")
app.include_router(tools.router)