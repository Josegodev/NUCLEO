from typing import Any

from pydantic import BaseModel, ConfigDict, Field

class ActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(min_length=1)
    payload: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
