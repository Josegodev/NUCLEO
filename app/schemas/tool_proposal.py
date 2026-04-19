from typing import Any

from pydantic import BaseModel, Field


class CapabilityGapSignal(BaseModel):
    type: str = "capability_gap_detected"
    capability_name: str
    reason: str
    proposal_generation_requested: bool = False


class ToolProposalModel(BaseModel):
    proposal_id: str
    name: str
    description: str
    purpose: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    read_only: bool
    side_effects: list[str] = Field(default_factory=list)
    capabilities_required: list[str] = Field(default_factory=list)
    risk_level: str
    timeout_s: int
    rationale: str
    example_usage: str
    status: str
    created_at: str
