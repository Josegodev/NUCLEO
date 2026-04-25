"""
Minimal in-memory runtime tracing.

This module is intentionally internal to the runtime. It does not persist data,
does not call external services, and does not decide whether tools may run.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Callable, Literal

from pydantic import BaseModel, Field


TracePhase = Literal["planner", "policy", "registry", "tool"]
TraceStatus = Literal["success", "error", "denied", "skipped"]


class ExecutionStep(BaseModel):
    step_id: str
    phase: TracePhase
    input: dict
    output: dict
    status: TraceStatus
    error: str | None = None
    timestamp: str


class ExecutionTrace(BaseModel):
    trace_id: str
    request_id: str | None = None
    steps: list[ExecutionStep] = Field(default_factory=list)


class Tracer(ABC):
    @abstractmethod
    def start_trace(self, request_id: str | None = None) -> ExecutionTrace:
        raise NotImplementedError

    @abstractmethod
    def record_step(self, trace: ExecutionTrace, step: ExecutionStep) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_trace(self, trace_id: str) -> ExecutionTrace | None:
        raise NotImplementedError


class InMemoryTracer(Tracer):
    def __init__(
        self,
        timestamp_provider: Callable[[], str] | None = None,
    ) -> None:
        self._traces: dict[str, ExecutionTrace] = {}
        self._sequence = 0
        self._timestamp_provider = timestamp_provider or self._utc_timestamp

    def start_trace(self, request_id: str | None = None) -> ExecutionTrace:
        trace_id = self._build_trace_id(request_id)
        trace = ExecutionTrace(trace_id=trace_id, request_id=request_id)
        self._traces[trace_id] = trace
        return trace

    def record_step(self, trace: ExecutionTrace, step: ExecutionStep) -> None:
        step_number = len(trace.steps) + 1
        completed_step = step.model_copy(
            update={
                "step_id": step.step_id or f"{step_number:03d}-{step.phase}",
                "timestamp": step.timestamp or self._timestamp_provider(),
            }
        )
        trace.steps.append(completed_step)
        self._traces[trace.trace_id] = trace

    def get_trace(self, trace_id: str) -> ExecutionTrace | None:
        return self._traces.get(trace_id)

    def _build_trace_id(self, request_id: str | None) -> str:
        if request_id:
            return f"trace-{request_id}"

        self._sequence += 1
        return f"trace-{self._sequence:06d}"

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
