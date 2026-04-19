# docs_esp Sync Audit

## Date

2026-04-19

## Purpose

Record the synchronization of `docs_esp/` with `docs/` so that the Spanish tree becomes a complete, maintained translation of the primary documentation set.

## Scope

- full inventory of `docs/`
- full inventory of `docs_esp/`
- one-to-one mapping between both trees
- controlled translation of missing or outdated content
- normalization of divergent filenames in `docs_esp/`

## Rule Applied

- `docs/` remains the source of truth
- `docs_esp/` must reflect `docs/` faithfully
- system component names remain in English
- unpaired legacy content is moved to `_deprecated/`

## Files Mapped

- `docs/architecture.md` -> `docs_esp/architecture.md`
- `docs/EVOLUTION_MAP.md` -> `docs_esp/EVOLUTION_MAP.md`
- `docs/vision/architecture_vision.md` -> `docs_esp/vision/architecture_vision.md`
- `docs/architecture/llm_tool_expansion.md` -> `docs_esp/architecture/llm_tool_expansion.md`
- `docs/planning/development_plan.md` -> `docs_esp/planning/development_plan.md`
- `docs/operations/operational_state.md` -> `docs_esp/operations/operational_state.md`
- `docs/operations/dev_state_snapshot.md` -> `docs_esp/operations/dev_state_snapshot.md`
- `docs/operations/session_log.md` -> `docs_esp/operations/session_log.md`
- `docs/operations/session_log_docs_normalization.md` -> `docs_esp/operations/session_log_docs_normalization.md`
- `docs/operations/session_log_llm_tool_expansion.md` -> `docs_esp/operations/session_log_llm_tool_expansion.md`
- `docs/operations/session_log_docs_esp_sync.md` -> `docs_esp/operations/session_log_docs_esp_sync.md`
- `docs/modules/agent_service.md` -> `docs_esp/modules/agent_service.md`
- `docs/modules/orchestrator.md` -> `docs_esp/modules/orchestrator.md`
- `docs/modules/planner.md` -> `docs_esp/modules/planner.md`
- `docs/modules/policy_engine.md` -> `docs_esp/modules/policy_engine.md`
- `docs/modules/tool_registry.md` -> `docs_esp/modules/tool_registry.md`
- `docs/modules/base_tool.md` -> `docs_esp/modules/base_tool.md`
- `docs/modules/tool_proposal_service.md` -> `docs_esp/modules/tool_proposal_service.md`
- `docs/modules/tool_generation_service.md` -> `docs_esp/modules/tool_generation_service.md`
- `docs/modules/staging_registry.md` -> `docs_esp/modules/staging_registry.md`
- `docs/modules/audit_store.md` -> `docs_esp/modules/audit_store.md`
- `docs/audits/repo_audit.md` -> `docs_esp/audits/repo_audit.md`
- `docs/audits/files_audit.md` -> `docs_esp/audits/files_audit.md`
- `docs/audits/documentation_consistency_audit.md` -> `docs_esp/audits/documentation_consistency_audit.md`
- `docs/audits/docs_esp_sync_audit.md` -> `docs_esp/audits/docs_esp_sync_audit.md`

## Files Created in docs_esp

- `docs_esp/architecture/llm_tool_expansion.md`
- `docs_esp/operations/session_log_docs_normalization.md`
- `docs_esp/operations/session_log_llm_tool_expansion.md`
- `docs_esp/operations/session_log_docs_esp_sync.md`
- `docs_esp/modules/tool_proposal_service.md`
- `docs_esp/modules/tool_generation_service.md`
- `docs_esp/modules/staging_registry.md`
- `docs_esp/modules/audit_store.md`
- `docs_esp/audits/repo_audit.md`
- `docs_esp/audits/files_audit.md`
- `docs_esp/audits/documentation_consistency_audit.md`
- `docs_esp/audits/docs_esp_sync_audit.md`

## Files Updated in docs_esp

- `docs_esp/architecture.md`
- `docs_esp/EVOLUTION_MAP.md`
- `docs_esp/vision/architecture_vision.md`
- `docs_esp/planning/development_plan.md`
- `docs_esp/operations/operational_state.md`
- `docs_esp/operations/dev_state_snapshot.md`
- `docs_esp/operations/session_log.md`
- `docs_esp/modules/agent_service.md`
- `docs_esp/modules/orchestrator.md`
- `docs_esp/modules/planner.md`
- `docs_esp/modules/policy_engine.md`
- `docs_esp/modules/tool_registry.md`
- `docs_esp/modules/base_tool.md`

## Files Moved to Deprecated

- `docs_esp/audits/repo.audit.md` -> `docs_esp/_deprecated/audits/repo.audit.md`
- `docs_esp/audits/files.audit.md` -> `docs_esp/_deprecated/audits/files.audit.md`

## Issues Found

- `docs_esp/` did not cover the full `docs/` tree
- legacy filenames in `docs_esp/audits/` no longer matched primary naming
- experimental module coverage was incomplete
- earlier mirror notes were not enough to guarantee semantic parity

## Decisions Taken

- sync `docs_esp/` structurally one-to-one with `docs/`
- add a header to every translated file with source path and last sync date
- keep component and module names in English
- keep `docs/` as the primary verified source even after sync

## Unverifiable Content

- no new technical claims were introduced beyond what `docs/` already stated
- when `docs/` marks a capability as partial or not verified, `docs_esp/` preserves the same certainty level
