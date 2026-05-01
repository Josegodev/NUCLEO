> Archivo origen: `docs/modules/orchestrator.md`
> Última sincronización: `2026-05-01`

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
13. valida el payload planificado contra el contrato de la tool seleccionada
14. si `dry_run=True`, registra un paso de tool como `skipped` con `executed=False` y no ejecuta la tool
15. si `request.options.agent_mode == "proposal_only"`, persiste la proposal por `trace_id`
16. si no, ejecuta `tool.run(payload, context=context)`
17. valida la salida de la tool contra el contrato de la tool seleccionada
18. registra success o error para el paso de tool
19. devuelve `AgentResponse`

El runtime ejecuta una tool solo después de una acción válida y
`PolicyDecisionValue.ALLOW`. `dry_run=True` nunca llama a `tool.run(...)`.

## Modo proposal

Cuando `agent_mode="proposal_only"` y `dry_run=True`, el runtime devuelve una
proposal en lugar de ejecutar:

```text
executed=false
execution_allowed=false
execution_state=PROPOSED
```

La proposal se persiste mediante `ApprovalStore` usando el `trace_id` de la
respuesta. El registro persistido incluye:

- `trace_id`
- `user_input`
- `planned_action`
- `proposed_tool`
- `arguments`
- `policy_decision_initial`
- `created_at`
- `execution_state`

Esta persistencia es estado interno del runtime. El frontend no guarda ni edita
el payload ejecutable.

## Approval Gate

`AgentRuntime.approve(trace_id, approved, context)` implementa la ejecución
controlada de proposals persistidas.

Si `approved=false`:

- un registro `PROPOSED` pasa a `REJECTED`
- no se llama al planner
- no se llama al LLM
- no se ejecuta ninguna tool

Si `approved=true`:

- el runtime carga la proposal por `trace_id`
- reconstruye el `PlannedAction` persistido
- no llama al Planner
- no llama a ningún proveedor LLM
- reevalúa `PolicyEngine` con `dry_run=False`
- resuelve de nuevo la tool mediante `ToolRegistry`
- valida otra vez el payload persistido con `tool.validate_input(...)`
- ejecuta `tool.run(...)` solo si esas comprobaciones pasan

Estados usados por el gate:

- `PROPOSED`
- `APPROVED`
- `EXECUTED`
- `REJECTED`
- `DENIED`
- `ERROR`

Regla de idempotencia:

- si una proposal ya está `EXECUTED`, una segunda aprobación devuelve el estado
  existente y no llama de nuevo a `tool.run(...)`

`/agent/approve` no acepta `tool_name` ni payload desde cliente. El único
payload ejecutable es el persistido desde la proposal dry-run original.

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
- transición explícita proposal -> approval -> execution
- aprobación idempotente para proposals ya ejecutadas
- traza interna mínima para fases de planner, policy, registry y tool

## Limitaciones actuales

- la composición del runtime sigue ocurriendo en tiempo de importación
- la traza del runtime sigue siendo solo en memoria

## Etiqueta de estado

- Ruta de producción: implementada
- Endurecimiento de contratos de artefacto: implementado para las tools de producción actuales
- Approval Gate: implementado
