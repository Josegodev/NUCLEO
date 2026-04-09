from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.runtime.planner import Planner
from app.tools.registry import ToolRegistry
from app.tools.implementations.echo_tool import EchoTool

registry = ToolRegistry()
registry.register(EchoTool())

planner = Planner()


class AgentRuntime:
    def run(self, request: AgentRequest) -> AgentResponse:
        plan = planner.create_plan(request)

        tool_name = plan["tool"]
        tool_payload = plan["payload"]

        tool = registry.get(tool_name)
        if not tool:
            return AgentResponse(
                status="error",
                message=f"Planner requested unknown tool: {tool_name}"
            )

        result = tool.run(tool_payload)

        status = "dry_run_success" if request.dry_run else "success"

        return AgentResponse(
            status=status,
            message=str(result)
        )