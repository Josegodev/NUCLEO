> Archivo origen: `docs/audits/docs_esp_sync_audit.md`
> Última sincronización: `2026-04-19`

# Auditoría de sincronización de docs_esp

## Alcance

Sincronización estructural y de contenido entre `docs/` y `docs_esp/` para que `docs_esp/` funcione como traducción completa y mantenida de la documentación primaria.

## Regla aplicada

- `docs/` es la fuente de verdad
- `docs_esp/` debe reflejar `docs/` de forma fiel
- los nombres de componentes se mantienen en inglés cuando son nombres propios del sistema
- el contenido sin correspondencia se mueve a `_deprecated/` o `_review/`

## Mapa de correspondencia 1:1

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

## Archivos creados en docs_esp

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

## Archivos actualizados en docs_esp

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

## Archivos movidos a deprecated

- `docs_esp/audits/repo.audit.md` -> `docs_esp/_deprecated/audits/repo.audit.md`
- `docs_esp/audits/files.audit.md` -> `docs_esp/_deprecated/audits/files.audit.md`

## Discrepancias detectadas

- `docs_esp/` no cubría todos los documentos existentes en `docs/`
- `docs_esp/audits/` usaba nombres heredados (`repo.audit.md`, `files.audit.md`) que ya no coincidían con la estructura primaria
- varios documentos en `docs_esp/` reflejaban un estado previo, no la narrativa documental actual

## Decisiones tomadas

- sincronizar `docs_esp/` con estructura 1:1 respecto a `docs/`
- añadir cabecera en cada archivo traducido con archivo origen y fecha de sincronización
- mantener nombres de componentes y módulos en inglés
- mantener `docs/` como fuente primaria de verdad, incluso tras la sincronización

## Contenido no verificable

- no se añadió contenido nuevo no presente en `docs/`
- cuando `docs/` ya marcaba una capacidad como parcial o no verificada, `docs_esp/` conserva exactamente ese mismo nivel de certeza
