from typing import Any

from pydantic import BaseModel

class AgentResponse(BaseModel):
    status: str
    message: str
    result: Any | None = None
