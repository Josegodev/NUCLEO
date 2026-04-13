from app.schemas.context import ExecutionContext
from app.tools.base import BaseTool


class EchoTool(BaseTool):
    name = "echo"
    description = "A simple tool that returns the payload it receives."
    read_only = True
    risk_level = "low"

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        return {
            "echo": payload,
            "requested_by": context.username if context else None,
            "request_id": context.request_id if context else None,
        }