from fastapi import APIRouter

from app.tools.registry import ToolRegistry
from app.tools.implementations.echo_tool import EchoTool
from app.tools.implementations.system_info_tool import SystemInfoTool

router = APIRouter()

registry = ToolRegistry()
registry.register(EchoTool())
registry.register(SystemInfoTool())


@router.get("/tools")
def list_tools():
    tools = registry.list_tools()

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "read_only": tool.read_only,
            "risk_level": tool.risk_level,
        }
        for tool in tools
    ]