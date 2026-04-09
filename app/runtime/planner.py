from app.schemas.requests import AgentRequest


class Planner:
    def create_plan(self, request: AgentRequest) -> dict:
        normalized_input = request.user_input.strip().lower()

        if "system" in normalized_input or "info" in normalized_input:
            return {
                "tool": "system_info",
                "payload": {}
            }

        return {
            "tool": "echo",
            "payload": {
                "text": request.user_input
            }
        }