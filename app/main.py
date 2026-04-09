from fastapi import FastAPI

from app.api.routes import health, agent

app = FastAPI()

app.include_router(health.router)
app.include_router(agent.router, prefix="/agent")