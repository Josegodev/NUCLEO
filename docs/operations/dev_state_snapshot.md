# Development State Snapshot - NUCLEO

## Snapshot Date

2026-04-19

## Purpose

Capture a concise point-in-time view of repository state after the introduction of the experimental lab path and the documentation normalization pass.

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

## Current Gaps

- planner contract still implicit
- dry-run not yet enforced structurally
- runtime error model still limited
- lab artifact persistence behavior depends on environment write permissions and has not been fully validated in this repository session

## Documentation Convention Snapshot

- `docs/` = primary source of truth
- `docs_esp/` = maintained translation of `docs/`, but not the primary source of verified truth
- new consistency audit stored in `docs/audits/documentation_consistency_audit.md`
