from typing import Any

from pydantic import BaseModel

class AgentRequest(BaseModel):
    user_input: str | None = None
    tool: str | None = None
    payload: dict[str, Any] | None = None
    dry_run: bool = True
    experimental_tool_generation: bool = False
