# Development State Snapshot - NUCLEO

## Snapshot Date

2026-04-19

## Current HARDENING Addendum

Updated on 2026-04-25 after `llm_lab` was added inside the repository.

This file still preserves the 2026-04-19 snapshot below as history. Current
verified behavior is:

- phase: HARDENING
- canonical flow:
  `Request -> API/FastAPI -> AgentService -> AgentRuntime/Orchestrator -> Planner -> PolicyEngine -> ToolRegistry -> Tool -> AgentResponse`
- production tools:
  - `echo`
  - `system_info`
  - `disk_info`
- Planner returns only `planned` or `no_plan`
- `dry_run=True` evaluates planner, policy, and registry, but does not call
  `Tool.run(...)`
- runtime tracing is internal and in-memory only
- `AgentResponse` exposes `status`, `message`, and optional `result`
- `runtime_lab/llm_lab/` is a lateral experimental observation path only
- Mistral/Qwen are not integrated with AgentService, Runtime, Planner,
  PolicyEngine, ToolRegistry, or Tools
- no LLM executes tools or calls `/agent/run` automatically

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
  - `message`
  - `result` optional

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

- planner contract still implicit
- dry-run was not yet enforced structurally at this historical snapshot date;
  current behavior enforces it in `AgentRuntime`
- runtime error model still limited
- lab artifact persistence behavior depends on environment write permissions and has not been fully validated in this repository session

## Documentation Convention Snapshot

- `docs/` = primary source of truth
- `docs_esp/` = maintained translation of `docs/`, but not the primary source of verified truth
- new consistency audit stored in `docs/audits/documentation_consistency_audit.md`
