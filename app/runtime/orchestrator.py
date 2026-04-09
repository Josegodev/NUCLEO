from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse

class AgentRuntime:
    def run(self, request: AgentRequest) -> AgentResponse:
        if request.dry_run:
            return AgentResponse(
                status="dry_run_success",
                message=f"Dry run: Agent would process '{request.user_input}'"
            )
        else:
            # Actual agent logic would go here
            return AgentResponse(
                status="success",
                message=f"Agent processed: '{request.user_input}'"
            )