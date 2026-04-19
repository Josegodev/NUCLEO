from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class StagingRecord:
    """State tracked by the isolated staging registry."""

    proposal_id: str
    tool_name: str
    status: str
    proposal_path: str
    generated_path: str | None = None
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
