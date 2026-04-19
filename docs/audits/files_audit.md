# Files Audit

## Layer

Audit

## Purpose

Track which technical files and modules are covered by documentation or repository audit.

## Covered Production Runtime Modules

- `app/services/agent_service.py`
- `app/runtime/orchestrator.py`
- `app/runtime/planner.py`
- `app/policies/engine.py`
- `app/tools/base.py`
- `app/tools/registry.py`

## Covered Experimental Lab Modules

- `app/services/tool_proposal/tool_proposal_service.py`
- `app/services/tool_generation/tool_generation_service.py`
- `app/services/staging/staging_registry.py`
- `app/services/audit/audit_store.py`
- `app/domain/tool_proposals/models.py`
- `app/domain/staging/models.py`
- `app/schemas/tool_proposal.py`

## Structurally Reviewed

- `app/main.py`
- `app/api/routes/*`
- `app/api/deps/auth.py`
- `app/schemas/*`
- `app/runtime/dispatcher.py`
- `runtime_lab/*`

## Summary

Repository coverage is sufficient to describe the stable execution path and the current isolated lab path. The main remaining documentation risk is historical drift across files rather than lack of module coverage.
