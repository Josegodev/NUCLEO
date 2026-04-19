> Archivo origen: `docs/operations/dev_state_snapshot.md`
> Última sincronización: `2026-04-19`

# Snapshot del estado de desarrollo - NUCLEO

## Fecha del snapshot

2026-04-19

## Propósito

Capturar una vista puntual y concisa del estado del repositorio tras la introducción de la ruta experimental de laboratorio y la pasada de normalización documental.

## Forma actual verificada del runtime

- backend FastAPI
- autenticación por API key con alcance de request
- propagación de `ExecutionContext`
- runtime de producción:
  - planner
  - policy
  - registry
  - tools
- tools de producción:
  - `echo`
  - `system_info`
- la respuesta contiene:
  - `status`
  - `message`
  - `result` opcional

## Adiciones experimentales verificadas

- `app/domain/tool_proposals/`
- `app/domain/staging/`
- `app/services/tool_proposal/`
- `app/services/tool_generation/`
- `app/services/staging/`
- `app/services/audit/`
- `runtime_lab/`

Estas adiciones están aisladas de la activación del registry de producción.

## Gaps actuales

- el contrato del planner sigue siendo implícito
- dry-run aún no se impone estructuralmente
- el modelo de errores del runtime sigue siendo limitado
- el comportamiento de persistencia de artefactos del laboratorio depende de permisos de escritura del entorno y no se validó completamente en esta sesión del repositorio

## Snapshot de convención documental

- `docs/` = fuente primaria de verdad
- `docs_esp/` = traducción mantenida de `docs/`, pero no fuente primaria de verdad verificada
- nueva auditoría de consistencia almacenada en `docs/audits/documentation_consistency_audit.md`
