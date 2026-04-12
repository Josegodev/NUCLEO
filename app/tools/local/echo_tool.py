from app.tools.base import BaseTool


class EchoTool(BaseTool):
    name = "echo"
    description = "A simple tool that returns the payload it receives."
    read_only = True
    risk_level = "low"

    def run(self, payload: dict) -> dict:
        return payload