# Planner v1:
# Always routes input to "echo" tool.
# Future: add decision logic or LLM-based planning.

from app.schemas.requests import AgentRequest


class Planner:
    def create_plan(self, request: AgentRequest) -> dict:
        return {
            "tool": "echo",
            "payload": {
                "text": request.user_input
            }
        }