> Archivo origen: `docs/audits/files_audit.md`
> Última sincronización: `2026-04-19`

# Auditoría de ficheros

## Capa

Auditoría

## Propósito

Registrar qué ficheros técnicos y módulos están cubiertos por documentación o por auditoría del repositorio.

## Módulos cubiertos del runtime de producción

- `app/services/agent_service.py`
- `app/runtime/orchestrator.py`
- `app/runtime/planner.py`
- `app/policies/engine.py`
- `app/tools/base.py`
- `app/tools/registry.py`

## Módulos cubiertos del laboratorio experimental

- `app/services/tool_proposal/tool_proposal_service.py`
- `app/services/tool_generation/tool_generation_service.py`
- `app/services/staging/staging_registry.py`
- `app/services/audit/audit_store.py`
- `app/domain/tool_proposals/models.py`
- `app/domain/staging/models.py`
- `app/schemas/tool_proposal.py`

## Revisado estructuralmente

- `app/main.py`
- `app/api/routes/*`
- `app/api/deps/auth.py`
- `app/schemas/*`
- `app/runtime/dispatcher.py`
- `runtime_lab/*`

## Resumen

La cobertura del repositorio es suficiente para describir la ruta estable de ejecución y la ruta actual aislada de laboratorio. El principal riesgo documental que permanece es la deriva histórica entre archivos, más que la falta de cobertura de módulos.
