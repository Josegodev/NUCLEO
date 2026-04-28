> Archivo origen: `docs/operations/dev_state_snapshot.md`
> Última sincronización: `2026-04-28`

# Snapshot del estado de desarrollo - NUCLEO

## Fecha del snapshot

2026-04-19

## Suplemento actual HARDENING

Actualizado el 2026-04-28 tras endurecer los contratos de artefactos.

Este archivo conserva debajo el snapshot del 2026-04-19 como historia. El
comportamiento verificado actual es:

- fase: HARDENING
- flujo canónico:
  `Request -> API/FastAPI -> AgentService -> AgentRuntime/Orchestrator -> Planner -> PolicyEngine -> ToolRegistry -> Tool -> AgentResponse`
- tools de producción:
  - `echo`
  - `system_info`
  - `disk_info`
- el Planner solo devuelve `planned` o `no_plan`
- `PlannedAction` está versionado e incluye precondiciones y salida esperada
- `PolicyDecision` es estricto, basado en enum y prohíbe campos extra
- `PolicyValidatedField` es un enum cerrado
- `ToolContractArtifact` es obligatorio para registrar tools de producción
- `dry_run=True` evalúa planner, policy y registry, pero no llama a
  `Tool.run(...)`
- la traza del runtime es interna y solo en memoria
- `AgentResponse` expone `status`, `result` estructurado opcional, `errors`,
  `trace_id` y `version`
- los estados públicos de ejecución están cerrados a `success`, `error` y
  `rejected`
- breaking change: `message` ya no es el contrato público de respuesta
- `runtime_lab/llm_lab/` es solo una ruta lateral experimental de observación
- Mistral/Qwen no están integrados con AgentService, Runtime, Planner,
  PolicyEngine, ToolRegistry ni Tools
- ningún LLM ejecuta tools ni llama automáticamente a `/agent/run`

## Propósito

Capturar una vista puntual y concisa del estado del repositorio tras la introducción de la ruta experimental de laboratorio y la pasada de normalización documental.

## Estado actual

Snapshot histórico solamente. Para el comportamiento verificado actual, usar `docs/operations/operational_state.md` y `docs/architecture.md`.

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
  - `disk_info`
- la respuesta contiene:
  - `status`
  - `result` opcional
  - `errors`
  - `trace_id`
  - `version`

## Adiciones experimentales verificadas

- `app/domain/tool_proposals/`
- `app/domain/staging/`
- `app/services/tool_proposal/`
- `app/services/tool_generation/`
- `app/services/staging/`
- `app/services/audit/`
- `runtime_lab/`

Estas adiciones están aisladas de la activación del registry de producción.

## Gaps históricos en la fecha del snapshot

- el contrato del planner era implícito en la fecha histórica del snapshot; el
  comportamiento actual usa `PlannedAction` versionado
- dry-run aún no se imponía estructuralmente en la fecha histórica del
  snapshot; el comportamiento actual sí lo impone en `AgentRuntime`
- el modelo de errores del runtime era limitado en la fecha histórica del
  snapshot; el comportamiento actual devuelve artefactos estructurados de
  resultado de ejecución
- el comportamiento de persistencia de artefactos del laboratorio depende de permisos de escritura del entorno y no se validó completamente en esta sesión del repositorio

## Snapshot de convención documental

- `docs/` = fuente primaria de verdad
- `docs_esp/` = traducción mantenida de `docs/`, pero no fuente primaria de verdad verificada
- nueva auditoría de consistencia almacenada en `docs/audits/documentation_consistency_audit.md`
