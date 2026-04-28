> Archivo origen: `docs/modules/orchestrator.md`
> Última sincronización: `2026-04-28`

# AgentRuntime

## Capa

Arquitectura verificada

## Propósito

Orquestador central de ejecución del runtime de producción.

## Comportamiento actual verificado

`AgentRuntime.run(request, context)` actualmente:

1. inicia una traza interna en memoria
2. pide al planner un `PlannedAction`
3. registra el paso del planner
4. valida que el planner devolvió un `PlannedAction` versionado
5. si el plan es `no_plan`, devuelve una respuesta estructurada `rejected`
6. si no, extrae `tool_name` y `payload`
7. pide autorización al `PolicyEngine`
8. registra el paso de policy
9. si la policy deniega, devuelve `rejected` estructurado
10. resuelve la tool desde el `ToolRegistry` de producción
11. registra el paso del registry
12. si falta, registra el paso como `error` y devuelve `error` estructurado
13. si `dry_run=True`, registra un paso de tool como `skipped` con `executed=False` y no ejecuta la tool
14. si no, ejecuta `tool.run(payload, context=context)`
15. valida la salida de la tool contra el contrato de la tool seleccionada
16. registra success o error para el paso de tool
17. devuelve `AgentResponse`

El runtime ejecuta una tool solo después de una acción válida y
`PolicyDecisionValue.ALLOW`. `dry_run=True` nunca llama a `tool.run(...)`.

`AgentResponse.status` público está cerrado a:

- `success`
- `error`
- `rejected`

Breaking change: `AgentResponse.message` ya no forma parte del contrato público.
El artefacto de resultado de ejecución usa `status`, `result`, `errors`,
`trace_id` y `version`.

## Fortalezas actuales

- pipeline de producción claro
- comprobación explícita de policy antes de ejecutar una tool de producción
- manejo explícito de tool de producción ausente
- traza interna mínima para fases de planner, policy, registry y tool

## Limitaciones actuales

- la composición del runtime sigue ocurriendo en tiempo de importación
- la traza del runtime sigue siendo solo en memoria

## Etiqueta de estado

- Ruta de producción: implementada
- Endurecimiento de contratos de artefacto: implementado para las tools de producción actuales
