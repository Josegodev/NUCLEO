from typing import Any, Dict, Literal

from pydantic import BaseModel, Field, model_validator


PlanStatus = Literal["planned", "no_plan"]


class PlanStep(BaseModel):
    tool_name: str
    payload: Dict[str, Any]


class ToolResult(BaseModel):
    tool_name: str
    output: Dict[str, Any]
    success: bool = True


class PlannedAction(BaseModel):
    tool_name: str | None = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: PlanStatus
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str
    source: str

    @model_validator(mode="after")
    def validate_planned_action_contract(self) -> "PlannedAction":
        if self.status == "planned" and not self.tool_name:
            raise ValueError("planned action requires tool_name")

        if self.status == "no_plan" and self.tool_name is not None:
            raise ValueError("no_plan action must not include tool_name")

        return self
