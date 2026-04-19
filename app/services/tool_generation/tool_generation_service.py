from __future__ import annotations

import json
from pathlib import Path

from app.schemas.tool_proposal import ToolProposalModel
from app.services.audit.audit_store import AuditStore


class ToolGenerationService:
    """Creates isolated experimental tool skeletons from staged proposals."""

    def __init__(
        self,
        generated_tools_dir: str | Path = "runtime_lab/generated_tools",
        audit_store: AuditStore | None = None,
    ) -> None:
        self.generated_tools_dir = Path(generated_tools_dir)
        self.generated_tools_dir.mkdir(parents=True, exist_ok=True)
        self.audit_store = audit_store or AuditStore()

    def generate_from_proposal(self, proposal: ToolProposalModel) -> dict[str, str]:
        tool_dir = self.generated_tools_dir / proposal.name
        tool_dir.mkdir(parents=True, exist_ok=True)

        tool_file = tool_dir / f"{proposal.name}_tool.py"
        tests_file = tool_dir / f"test_{proposal.name}_tool.py"
        metadata_file = tool_dir / "metadata.json"

        tool_file.write_text(self._build_tool_skeleton(proposal), encoding="utf-8")
        tests_file.write_text(self._build_test_skeleton(proposal), encoding="utf-8")
        metadata_file.write_text(
            json.dumps(
                {
                    "proposal_id": proposal.proposal_id,
                    "name": proposal.name,
                    "status": proposal.status,
                    "generated_for_lab": True,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        artifact_paths = {
            "tool_dir": str(tool_dir),
            "tool_file": str(tool_file),
            "tests_file": str(tests_file),
            "metadata_file": str(metadata_file),
        }
        self.audit_store.record(
            event="tool_skeleton_generated",
            proposal_id=proposal.proposal_id,
            action="generate_tool_skeleton",
            result="success",
            artifact_paths=list(artifact_paths.values()),
            metadata={"tool_name": proposal.name},
        )
        return artifact_paths

    @staticmethod
    def _build_tool_skeleton(proposal: ToolProposalModel) -> str:
        return f'''"""Experimental tool skeleton generated in runtime_lab.

This file is not auto-registered in the production ToolRegistry.
Review and promote manually if needed.
"""

from app.schemas.context import ExecutionContext
from app.tools.base import BaseTool


class {ToolGenerationService._class_name(proposal.name)}(BaseTool):
    name = "{proposal.name}"
    description = "{proposal.description}"
    read_only = {proposal.read_only}
    risk_level = "{proposal.risk_level}"

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        """Implement lab-only behavior after manual review."""
        return {{
            "status": "not_implemented",
            "proposal_id": "{proposal.proposal_id}",
            "payload": payload,
            "requested_by": context.username if context else None,
        }}
'''

    @staticmethod
    def _build_test_skeleton(proposal: ToolProposalModel) -> str:
        class_name = ToolGenerationService._class_name(proposal.name)
        return f"""from {proposal.name}_tool import {class_name}


def test_{proposal.name}_tool_placeholder():
    tool = {class_name}()
    result = tool.run({{"request_text": "example"}})

    assert result["status"] == "not_implemented"
    assert result["proposal_id"] == "{proposal.proposal_id}"
"""

    @staticmethod
    def _class_name(tool_name: str) -> str:
        return "".join(part.capitalize() for part in tool_name.split("_")) + "Tool"
