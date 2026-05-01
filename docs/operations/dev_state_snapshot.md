# Development State Snapshot - NUCLEO

## Snapshot Date

2026-04-19

## Current HARDENING Addendum

Updated on 2026-05-01 after LLM Planner augmentation and Approval Gate
documentation sync.

This file still preserves the 2026-04-19 snapshot below as history. Current
verified behavior is:

- phase: HARDENING
- canonical flow:
  `Request -> API/FastAPI -> AgentService -> AgentRuntime/Orchestrator -> Planner -> PolicyEngine -> ToolRegistry -> Tool or dry-run proposal -> AgentResponse`
- production tools:
  - `echo`
  - `system_info`
  - `disk_info`
- Planner returns only `planned` or `no_plan`
- controlled LLM-assisted planning is active for `agent_mode=proposal_only`
- `PlannedAction` is versioned and carries preconditions plus expected output
- `PolicyDecision` is strict, enum-backed, and forbids extra fields
- `PolicyValidatedField` is a closed enum
- `ToolContractArtifact` is required for production tool registration
- `dry_run=True` evaluates planner, policy, and registry, but does not call
  `Tool.run(...)` or `tool.run(...)`
- runtime tracing is internal and in-memory only
- `AgentResponse` exposes `status`, optional structured `result`, `errors`,
  `trace_id`, and `version`
- public execution statuses are closed to `success`, `error`, and `rejected`
- breaking change: `message` is no longer the public response contract
- `runtime_lab/llm_lab/` is a lateral experimental observation path only
- `app/adapters/model_router.py` reuses `runtime_lab/llm_lab/model_adapter.py`
  as a model-provider adapter for controlled Planner augmentation
- no LLM executes tools or calls `/agent/run` automatically
- `/agent/approve` executes only persisted proposals and does not call Planner
  or LLM

## Purpose

Capture a concise point-in-time view of repository state after the introduction of the experimental lab path and the documentation normalization pass.

## Current Status

Historical snapshot only. For current verified behavior, use `docs/operations/operational_state.md` and `docs/architecture.md`.

## Verified Current Runtime Shape

- FastAPI backend
- request-scoped API key authentication
- `ExecutionContext` propagation
- production runtime:
  - planner
  - policy
  - registry
  - tools
- production tools:
  - `echo`
  - `system_info`
  - `disk_info`
- response carries:
  - `status`
  - `result` optional
  - `errors`
  - `trace_id`
  - `version`

## Verified Experimental Additions

- `app/domain/tool_proposals/`
- `app/domain/staging/`
- `app/services/tool_proposal/`
- `app/services/tool_generation/`
- `app/services/staging/`
- `app/services/audit/`
- `runtime_lab/`

These additions are isolated from production registry activation.

## Historical Gaps At Snapshot Date

- planner contract was implicit at this historical snapshot date; current
  behavior uses versioned `PlannedAction`
- dry-run was not yet enforced structurally at this historical snapshot date;
  current behavior enforces it in `AgentRuntime`
- runtime error model was limited at this historical snapshot date; current
  behavior returns structured execution-result artifacts
- lab artifact persistence behavior depends on environment write permissions and has not been fully validated in this repository session

## Documentation Convention Snapshot

- `docs/` = primary source of truth
- `docs_esp/` = maintained translation of `docs/`, but not the primary source of verified truth
- new consistency audit stored in `docs/audits/documentation_consistency_audit.md`
