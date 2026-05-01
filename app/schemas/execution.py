from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.artifacts import (
    JsonValue,
    ToolName,
    ToolPrecondition,
    action_preconditions,
    expected_output_schema,
    validate_tool_payload,
)


PlanStatus = Literal["planned", "no_plan"]
PlanSource = Literal[
    "explicit_request",
    "rule:disk_info",
    "rule:system_info",
    "rule_table",
    "llm_assisted",
]


class PlanStep(BaseModel):
    tool_name: ToolName
    payload: dict[str, JsonValue]


class ToolResult(BaseModel):
    tool_name: ToolName
    output: dict[str, JsonValue]
    success: bool = True


class PlannedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: ToolName | None = None
    payload: dict[str, JsonValue] = Field(default_factory=dict)
    status: PlanStatus
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    source: PlanSource
    preconditions: list[ToolPrecondition] = Field(default_factory=list)
    expected_output: dict[str, JsonValue] = Field(default_factory=dict)
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
    version: Literal["action.v1"] = "action.v1"

    @model_validator(mode="after")
    def validate_planned_action_contract(self) -> "PlannedAction":
        if self.status == "planned" and not self.tool_name:
            raise ValueError("planned action requires tool_name")

        if self.status == "planned":
            self.payload = validate_tool_payload(self.tool_name, self.payload)
            if not self.preconditions:
                self.preconditions = action_preconditions(self.tool_name)
            if not self.expected_output:
                self.expected_output = expected_output_schema(self.tool_name)

        if self.status == "no_plan" and self.tool_name is not None:
            raise ValueError("no_plan action must not include tool_name")

        if self.status == "no_plan" and self.preconditions:
            raise ValueError("no_plan action must not include preconditions")

        if self.status == "no_plan" and self.expected_output:
            raise ValueError("no_plan action must not include expected_output")

        return self
