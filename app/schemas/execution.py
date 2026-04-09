from pydantic import BaseModel
from typing import Any, Dict


class PlanStep(BaseModel):
    tool_name: str
    payload: Dict[str, Any]


class ToolResult(BaseModel):
    tool_name: str
    output: Dict[str, Any]
    success: bool = True