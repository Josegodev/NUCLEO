from __future__ import annotations

import json
from pathlib import Path

from app.domain.staging.models import StagingRecord
from app.schemas.tool_proposal import ToolProposalModel
from app.services.audit.audit_store import AuditStore


class StagingRegistry:
    """JSON-backed registry for experimental proposals only."""

    VALID_STATUSES = {"draft", "generated", "reviewed", "approved", "rejected"}

    def __init__(
        self,
        registry_dir: str | Path = "runtime_lab/staging_registry",
        audit_store: AuditStore | None = None,
    ) -> None:
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.registry_dir / "registry.json"
        self.audit_store = audit_store or AuditStore()

    def register_proposal(
        self,
        proposal: ToolProposalModel,
        proposal_path: str,
    ) -> StagingRecord:
        record = StagingRecord(
            proposal_id=proposal.proposal_id,
            tool_name=proposal.name,
            status="draft",
            proposal_path=proposal_path,
        )
        data = self._load_all()
        data.append(record.__dict__)
        self._save_all(data)
        self.audit_store.record(
            event="staging_registry_updated",
            proposal_id=proposal.proposal_id,
            action="register_proposal",
            result="success",
            artifact_paths=[proposal_path, str(self.registry_file)],
            metadata={"status": "draft", "tool_name": proposal.name},
        )
        return record

    def update_status(
        self,
        proposal_id: str,
        status: str,
        generated_path: str | None = None,
    ) -> dict:
        if status not in self.VALID_STATUSES:
            raise ValueError(f"unsupported staging status: {status}")

        data = self._load_all()
        for record in data:
            if record["proposal_id"] == proposal_id:
                record["status"] = status
                if generated_path is not None:
                    record["generated_path"] = generated_path
                self._save_all(data)
                self.audit_store.record(
                    event="staging_status_changed",
                    proposal_id=proposal_id,
                    action="update_status",
                    result="success",
                    artifact_paths=[str(self.registry_file)],
                    metadata={
                        "status": status,
                        "generated_path": generated_path,
                    },
                )
                return record
        raise KeyError(f"proposal not found in staging registry: {proposal_id}")

    def list_proposals(self) -> list[dict]:
        return self._load_all()

    def _load_all(self) -> list[dict]:
        if not self.registry_file.exists():
            return []
        return json.loads(self.registry_file.read_text(encoding="utf-8"))

    def _save_all(self, data: list[dict]) -> None:
        self.registry_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
