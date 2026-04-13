# Files Audit

## Purpose

Track which parts of the repository have been audited.

This document does not duplicate detailed audits.
It only indicates coverage and references.

---

## Audited Modules

- `app/services/agent_service.py` → see `docs/modules/agent_service.md`
- `app/runtime/orchestrator.py` → see `docs/modules/orchestrator.md`
- `app/runtime/planner.py` → see `docs/modules/planner.md`
- `app/policies/engine.py` → see `docs/modules/policy_engine.md`
- `app/tools/base.py` → see `docs/modules/base_tool.md`
- `app/tools/registry.py` → see `docs/modules/tool_registry.md`

---

## Structurally Reviewed

- `app/main.py`
- `app/api/routes/*`
- `app/policies/models.py`
- `app/schemas/*`
- `app/runtime/dispatcher.py`

(covered in `repo_audit.md`)

---

## Summary

The system is modular and correctly separated, but relies heavily on implicit contracts:

- planner → runtime contract is not validated
- tool input/output is not structured
- policy does not enforce execution modes
- runtime does not handle failures

The architecture is sound, but still in a bootstrap stage.