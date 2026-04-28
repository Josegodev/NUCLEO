from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.artifacts import JsonValue


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    REJECTED = "rejected"


class ExecutionErrorCode(str, Enum):
    PLANNER_INVALID_RESULT = "planner_invalid_result"
    NO_PLAN = "no_plan"
    POLICY_INVALID_RESULT = "policy_invalid_result"
    POLICY_DENIED = "policy_denied"
    TOOL_NOT_FOUND = "tool_not_found"
    TOOL_INPUT_INVALID = "tool_input_invalid"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"
    TOOL_OUTPUT_INVALID = "tool_output_invalid"
    TOOL_REPORTED_ERROR = "tool_reported_error"


class ExecutionError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ExecutionErrorCode
    message: str = Field(min_length=1)
    field: str | None = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ExecutionStatus
    result: dict[str, JsonValue] | None = None
    errors: list[ExecutionError] = Field(default_factory=list)
    trace_id: str = Field(min_length=1)
    version: Literal["execution_result.v1"] = "execution_result.v1"

    @model_validator(mode="after")
    def validate_execution_result_contract(self) -> "AgentResponse":
        if self.status == ExecutionStatus.SUCCESS and self.errors:
            raise ValueError("successful execution result must not include errors")

        if self.status != ExecutionStatus.SUCCESS and not self.errors:
            raise ValueError("non-success execution result must include errors")

        return self
