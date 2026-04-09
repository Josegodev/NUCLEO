from fastapi import APIRouter
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.runtime.orchestrator import AgentRuntime

router = APIRouter()
runtime = AgentRuntime()

@router.post("/run", response_model=AgentResponse)
def run_agent(request: AgentRequest):
    return runtime.run(request)