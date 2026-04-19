from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import uuid4

from app.domain.tool_proposals.models import ToolProposal
from app.schemas.context import ExecutionContext
from app.schemas.tool_proposal import ToolProposalModel
from app.services.audit.audit_store import AuditStore


class ToolProposalService:
    """Deterministic placeholder service for capability-gap proposals."""

    def __init__(
        self,
        proposals_dir: str | Path = "runtime_lab/proposals",
        audit_store: AuditStore | None = None,
    ) -> None:
        self.proposals_dir = Path(proposals_dir)
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        self.audit_store = audit_store or AuditStore()

    def create_from_gap(
        self,
        user_input: str,
        capability_name: str,
        context: ExecutionContext,
    ) -> ToolProposalModel:
        proposal = ToolProposal(
            proposal_id=f"proposal-{uuid4().hex[:12]}",
            name=self._normalize_tool_name(capability_name),
            description=(
                "Experimental tool proposal generated from a detected capability gap."
            ),
            purpose=(
                f"Cover the missing capability inferred from request: {user_input}"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "request_text": {"type": "string"},
                },
                "required": ["request_text"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                },
                "required": ["result"],
            },
            read_only=True,
            side_effects=[],
            capabilities_required=[capability_name],
            risk_level="medium",
            timeout_s=30,
            rationale=(
                "The current production registry does not expose a tool that maps "
                "cleanly to the requested capability, so a staged proposal is created."
            ),
            example_usage=user_input,
        )
        model = ToolProposalModel.parse_obj(proposal.__dict__)
        proposal_path = self._write_proposal(model)
        self.audit_store.record(
            event="tool_proposal_created",
            proposal_id=model.proposal_id,
            action="create_proposal",
            result="success",
            artifact_paths=[str(proposal_path)],
            metadata={
                "tool_name": model.name,
                "requested_by": context.username,
                "capability_name": capability_name,
            },
        )
        return model

    def _write_proposal(self, proposal: ToolProposalModel) -> Path:
        proposal_path = self.proposals_dir / f"{proposal.proposal_id}.json"
        proposal_path.write_text(
            json.dumps(proposal.dict(), indent=2),
            encoding="utf-8",
        )
        return proposal_path

    @staticmethod
    def _normalize_tool_name(capability_name: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "_", capability_name.lower()).strip("_")
        return normalized or "generated_tool"
