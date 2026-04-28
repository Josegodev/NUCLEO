from fastapi import APIRouter

from app.tools.registry import registry

router = APIRouter()


@router.get("/tools")
def list_tools():
    tools = registry.list_tools()

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "read_only": tool.read_only,
            "risk_level": tool.risk_level,
            "contract": tool.contract.model_dump(mode="json"),
        }
        for tool in tools
    ]
