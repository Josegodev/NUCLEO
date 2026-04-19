from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class ToolProposal:
    """Domain entity describing a proposed experimental tool."""

    proposal_id: str
    name: str
    description: str
    purpose: str
    input_schema: dict
    output_schema: dict
    read_only: bool
    side_effects: list[str]
    capabilities_required: list[str]
    risk_level: str
    timeout_s: int
    rationale: str
    example_usage: str
    status: str = "draft"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
