from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.artifacts import JsonValue, ToolName


class ExecutionState(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    DENIED = "DENIED"
    ERROR = "ERROR"


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(min_length=1)
    approved: bool


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "denied", "error"]
    trace_id: str = Field(min_length=1)
    execution_state: ExecutionState
    tool: ToolName | None = None
    executed: bool = False
    result: dict[str, JsonValue] = Field(default_factory=dict)
    reason: str | None = None

