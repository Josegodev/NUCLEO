> Archivo origen: `docs/modules/orchestrator.md`
> Última sincronización: `2026-04-25`

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
4. valida que el planner devolvió `PlannedAction`
5. si el plan es `no_plan`, devuelve una respuesta controlada `no_plan`
6. si no, extrae `tool_name` y `payload`
7. pide autorización al `PolicyEngine`
8. registra el paso de policy
9. si la policy deniega, devuelve `blocked`
10. resuelve la tool desde el `ToolRegistry` de producción
11. registra el paso del registry
12. si falta, registra el paso como `error` y devuelve `error`
13. si `dry_run=True`, registra un paso de tool como `skipped` con `executed=False` y no ejecuta la tool
14. si no, ejecuta `tool.run(payload, context=context)`
15. registra success o error para el paso de tool
16. devuelve `AgentResponse`

## Fortalezas actuales

- pipeline de producción claro
- comprobación explícita de policy antes de ejecutar una tool de producción
- manejo explícito de tool de producción ausente
- traza interna mínima para fases de planner, policy, registry y tool

## Limitaciones actuales

- la composición del runtime sigue ocurriendo en tiempo de importación
- el manejo de excepciones es limitado
- la respuesta sigue duplicando datos entre `message` y `result`

## Etiqueta de estado

- Ruta de producción: implementada
- Endurecimiento completo de contratos: no implementado
