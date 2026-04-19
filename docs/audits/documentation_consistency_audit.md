# Documentation Consistency Audit

## Scope

Full Markdown audit for NUCLEO repository documentation, excluding third-party or environment-vendored Markdown under `.venv/`.

## Documentary Convention Applied

Documentation is normalized into these layers:

- Verified architecture
- Target architecture / vision
- Operations
- Audit
- Session log

Primary source of truth:

- `docs/`

Maintained translation:

- `docs_esp/`

When conflict exists between documentation and code, code is treated as the higher-confidence source.

## Inventory of Markdown Files

### Root

- `README.md` -> repository overview, quick start, verified runtime summary -> operation + entrypoint overview

### Primary docs

- `docs/architecture.md` -> verified architecture
- `docs/EVOLUTION_MAP.md` -> evolution roadmap from current state
- `docs/vision/architecture_vision.md` -> target architecture
- `docs/planning/development_plan.md` -> planned technical priorities
- `docs/operations/operational_state.md` -> current operational state
- `docs/operations/dev_state_snapshot.md` -> point-in-time implementation snapshot
- `docs/operations/session_log.md` -> historical engineering log
- `docs/operations/session_log_llm_tool_expansion.md` -> session log for lab subsystem
- `docs/modules/agent_service.md` -> module documentation
- `docs/modules/orchestrator.md` -> module documentation
- `docs/modules/planner.md` -> module documentation
- `docs/modules/policy_engine.md` -> module documentation
- `docs/modules/tool_registry.md` -> module documentation
- `docs/modules/base_tool.md` -> module documentation
- `docs/modules/tool_proposal_service.md` -> experimental module documentation
- `docs/modules/tool_generation_service.md` -> experimental module documentation
- `docs/modules/staging_registry.md` -> experimental module documentation
- `docs/modules/audit_store.md` -> experimental module documentation
- `docs/architecture/llm_tool_expansion.md` -> experimental architecture note
- `docs/audits/repo_audit.md` -> repository structure audit
- `docs/audits/files_audit.md` -> coverage audit
- `docs/audits/documentation_consistency_audit.md` -> documentation consistency audit

### Maintained translation

- `docs_esp/architecture.md`
- `docs_esp/EVOLUTION_MAP.md`
- `docs_esp/vision/architecture_vision.md`
- `docs_esp/architecture/llm_tool_expansion.md`
- `docs_esp/planning/development_plan.md`
- `docs_esp/operations/operational_state.md`
- `docs_esp/operations/dev_state_snapshot.md`
- `docs_esp/operations/session_log.md`
- `docs_esp/operations/session_log_docs_normalization.md`
- `docs_esp/operations/session_log_llm_tool_expansion.md`
- `docs_esp/operations/session_log_docs_esp_sync.md`
- `docs_esp/modules/agent_service.md`
- `docs_esp/modules/orchestrator.md`
- `docs_esp/modules/planner.md`
- `docs_esp/modules/policy_engine.md`
- `docs_esp/modules/tool_registry.md`
- `docs_esp/modules/base_tool.md`
- `docs_esp/modules/tool_proposal_service.md`
- `docs_esp/modules/tool_generation_service.md`
- `docs_esp/modules/staging_registry.md`
- `docs_esp/modules/audit_store.md`
- `docs_esp/audits/repo_audit.md`
- `docs_esp/audits/files_audit.md`
- `docs_esp/audits/documentation_consistency_audit.md`
- `docs_esp/audits/docs_esp_sync_audit.md`

## Contradictions Detected

### 1. Architecture current state vs historical auth notes

Conflict:
- `docs/architecture.md` mixed verified runtime notes with a historical auth-design section.

Decision:
- Normalize `docs/architecture.md` into verified architecture only.
- Keep auth as part of verified current state, not as a future note.

### 2. Response structure

Conflict:
- older docs stated response was only `status + message`
- code now includes optional `result`

Decision:
- all primary docs updated to describe `result` as current verified behavior
- historical logs preserved as logs, not current truth

### 3. ExecutionContext status

Conflict:
- some operational docs said “do not introduce ExecutionContext yet”
- code already includes request-scoped execution context

Decision:
- primary operational docs updated to current verified state
- historical statements retained only inside session log as historical context

### 4. Experimental lab path vs production path

Conflict:
- older docs did not mention experimental lab
- new docs described it, but not always distinguished from production flow

Decision:
- primary docs now separate:
  - stable production runtime
  - isolated experimental lab

### 5. Policy behavior

Conflict:
- several docs described whitelist-only policy
- code now also checks authentication and admin role for `system_info`

Decision:
- primary docs updated to reflect current verified policy behavior

### 6. Planner behavior

Conflict:
- older docs described only `system_info` / `echo` branch
- code now also has opt-in capability-gap signaling

Decision:
- primary docs updated to describe both:
  - stable production behavior
  - experimental opt-in branch

### 7. docs vs docs_esp

Conflict:
- `docs_esp/` was partial and could contradict primary docs

Decision:
- synchronize `docs_esp/` as a maintained translation of `docs/`
- keep `docs/` as the primary verified source

## Contradictions Not Fully Resolved

### runtime_lab persistence operability

Reason:
- code implements file-backed lab persistence
- repository session could not fully verify artifact writing behavior in current sandbox environment

Decision:
- document as implemented code path
- avoid claiming full operational verification

### dispatcher role

Reason:
- `runtime/dispatcher.py` exists but is not integrated in runtime flow

Decision:
- describe it as present but not integrated

## Redundant or Overlapping Documents

- `docs/operations/operational_state.md` and `docs/operations/dev_state_snapshot.md` overlap but now serve different scopes:
  - operational state = current operating model
  - dev snapshot = point-in-time implementation snapshot
- `docs/architecture.md` and `docs/vision/architecture_vision.md` overlap in topic but now differ clearly by time horizon
- `docs_esp/` overlaps with `docs/`, but is now treated as a maintained translation, not the primary verified documentation

## Recommended Documentation Hierarchy

1. `README.md` -> repository entry
2. `docs/architecture.md` -> verified architecture
3. `docs/vision/architecture_vision.md` -> future design
4. `docs/operations/*` -> state and logs
5. `docs/modules/*` -> component-level detail
6. `docs/audits/*` -> critical evaluation
7. `docs_esp/*` -> maintained translation

## Files Modified During Normalization

- `README.md`
- `docs/architecture.md`
- `docs/vision/architecture_vision.md`
- `docs/EVOLUTION_MAP.md`
- `docs/operations/operational_state.md`
- `docs/operations/dev_state_snapshot.md`
- `docs/operations/session_log.md`
- `docs/planning/development_plan.md`
- `docs/modules/agent_service.md`
- `docs/modules/orchestrator.md`
- `docs/modules/planner.md`
- `docs/modules/policy_engine.md`
- `docs/modules/tool_registry.md`
- `docs/modules/base_tool.md`
- `docs/audits/repo_audit.md`
- `docs/audits/files_audit.md`
- `docs/audits/documentation_consistency_audit.md`
- `docs/operations/session_log_docs_normalization.md`
- `docs_esp/*.md` files marked as translation mirror
