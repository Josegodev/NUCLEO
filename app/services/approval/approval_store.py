from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, ConfigDict, Field

from app.policies.models import PolicyDecision
from app.schemas.approval import ExecutionState
from app.schemas.artifacts import JsonValue, ToolName
from app.schemas.execution import PlannedAction


class ApprovalTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    previous_state: ExecutionState
    new_state: ExecutionState
    approval_decision: bool | None = None
    policy_decision_on_execution: dict[str, JsonValue] | None = None
    tool: ToolName | None = None
    executed: bool = False
    reason: str | None = None
    timestamp: str


class ApprovalProposalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = Field(min_length=1)
    user_input: str | None = None
    planned_action: dict[str, JsonValue]
    proposed_tool: ToolName
    arguments: dict[str, JsonValue]
    policy_decision_initial: dict[str, JsonValue]
    created_at: str
    execution_state: ExecutionState = ExecutionState.PROPOSED
    result: dict[str, JsonValue] = Field(default_factory=dict)
    reason: str | None = None
    transitions: list[ApprovalTransition] = Field(default_factory=list)


class ApprovalStore:
    """File-backed approval proposal store keyed by trace_id."""

    def __init__(self, approvals_dir: str | Path = "runtime_lab/approvals") -> None:
        self.approvals_dir = Path(approvals_dir)
        self.approvals_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def save_proposal(
        self,
        *,
        trace_id: str,
        user_input: str | None,
        planned_action: PlannedAction,
        policy_decision_initial: PolicyDecision,
    ) -> ApprovalProposalRecord:
        if planned_action.status != "planned" or planned_action.tool_name is None:
            raise ValueError("approval proposal requires a planned action")

        with self._lock:
            existing = self.get(trace_id)
            if existing is not None:
                return existing

            record = ApprovalProposalRecord(
                trace_id=trace_id,
                user_input=user_input,
                planned_action=planned_action.model_dump(mode="json"),
                proposed_tool=planned_action.tool_name,
                arguments=planned_action.payload,
                policy_decision_initial=policy_decision_initial.model_dump(mode="json"),
                created_at=self._utc_timestamp(),
                execution_state=ExecutionState.PROPOSED,
            )
            self._write(record)
            return record

    def get(self, trace_id: str) -> ApprovalProposalRecord | None:
        path = self._path_for(trace_id)
        if not path.exists():
            return None

        payload = json.loads(path.read_text(encoding="utf-8"))
        return ApprovalProposalRecord.model_validate(payload)

    def transition(
        self,
        *,
        trace_id: str,
        new_state: ExecutionState,
        approval_decision: bool | None = None,
        policy_decision_on_execution: dict[str, JsonValue] | None = None,
        tool: ToolName | None = None,
        executed: bool = False,
        reason: str | None = None,
        result: dict[str, JsonValue] | None = None,
    ) -> ApprovalProposalRecord | None:
        with self._lock:
            record = self.get(trace_id)
            if record is None:
                return None

            transition = ApprovalTransition(
                previous_state=record.execution_state,
                new_state=new_state,
                approval_decision=approval_decision,
                policy_decision_on_execution=policy_decision_on_execution,
                tool=tool,
                executed=executed,
                reason=reason,
                timestamp=self._utc_timestamp(),
            )
            updated = record.model_copy(
                deep=True,
                update={
                    "execution_state": new_state,
                    "result": result if result is not None else record.result,
                    "reason": reason,
                    "transitions": [*record.transitions, transition],
                },
            )
            self._write(updated)
            return updated

    def transition_if_state(
        self,
        *,
        trace_id: str,
        expected_state: ExecutionState,
        new_state: ExecutionState,
        approval_decision: bool | None = None,
        policy_decision_on_execution: dict[str, JsonValue] | None = None,
        tool: ToolName | None = None,
        executed: bool = False,
        reason: str | None = None,
        result: dict[str, JsonValue] | None = None,
    ) -> tuple[ApprovalProposalRecord | None, bool]:
        with self._lock:
            record = self.get(trace_id)
            if record is None:
                return None, False
            if record.execution_state != expected_state:
                return record, False

            transition = ApprovalTransition(
                previous_state=record.execution_state,
                new_state=new_state,
                approval_decision=approval_decision,
                policy_decision_on_execution=policy_decision_on_execution,
                tool=tool,
                executed=executed,
                reason=reason,
                timestamp=self._utc_timestamp(),
            )
            updated = record.model_copy(
                deep=True,
                update={
                    "execution_state": new_state,
                    "result": result if result is not None else record.result,
                    "reason": reason,
                    "transitions": [*record.transitions, transition],
                },
            )
            self._write(updated)
            return updated, True

    def _write(self, record: ApprovalProposalRecord) -> None:
        self._path_for(record.trace_id).write_text(
            record.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def _path_for(self, trace_id: str) -> Path:
        safe_trace_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", trace_id)
        return self.approvals_dir / f"{safe_trace_id}.json"

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
