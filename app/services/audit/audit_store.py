from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class AuditStore:
    """Simple file-based audit trail for lab workflows."""

    def __init__(self, audit_dir: str | Path = "runtime_lab/audit") -> None:
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        event: str,
        proposal_id: str,
        action: str,
        result: str,
        artifact_paths: list[str],
        metadata: dict | None = None,
    ) -> Path:
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = {
            "event": event,
            "timestamp": timestamp,
            "proposal_id": proposal_id,
            "action": action,
            "result": result,
            "artifact_paths": artifact_paths,
            "metadata": metadata or {},
        }
        filename = f"{timestamp.replace(':', '-').replace('.', '-')}_{proposal_id}_{uuid4().hex[:8]}.json"
        path = self.audit_dir / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
