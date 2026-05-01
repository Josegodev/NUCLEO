> Archivo origen: `docs/modules/planner.md`
> Última sincronización: `2026-05-01`

# Planner

## Capa

Arquitectura verificada

## Propósito

Transformar un `AgentRequest` en una acción candidata determinista.

El planner propone. No autoriza, no resuelve la verdad de runtime y no ejecuta.

## Comportamiento actual verificado

El planner actualmente:

1. normaliza `request.user_input` con `strip().lower()`
2. si `request.tool` está definido y la tool existe en `ToolRegistry`, devuelve `planned`
3. evalúa una pequeña tabla explícita de reglas deterministas
4. si una regla encaja y su tool existe en `ToolRegistry`, devuelve `planned`
5. si no, devuelve `no_plan`

## Contrato observado en código

La salida actual es `PlannedAction`.

Campos:

- `status`
- `tool_name`
- `payload`
- `confidence`
- `reason`
- `source`

Estados:

- `planned`
- `no_plan`

`no_plan` es esperado cuando ninguna regla determinista encaja.

## Fortalezas

- determinista
- sin efectos laterales en la ruta de producción
- fácil de leer
- las reglas están en una tabla explícita y auditable
- comprueba que las tools objetivo existen en `ToolRegistry`
- el runtime recibe un contrato tipado en lugar de un dict implícito

## Limitaciones actuales

- la lógica de matching es débil y basada en heurísticas
- persiste un acoplamiento fuerte a nombres literales de tools de producción

## Planner Contract - HARDENING

El contrato del planner queda cerrado alrededor de una sola responsabilidad:

```text
AgentRequest -> PlannerStrategy -> PlannedAction
```

`PlannerStrategy` recibe un `AgentRequest` y debe devolver un `PlannedAction`
válido. El wrapper público `Planner` comprueba esta frontera antes de devolver
el plan a `AgentRuntime`.

El único orden válido de ejecución en producción sigue siendo:

```text
Planner -> PolicyEngine -> ToolRegistry -> Tool
```

Comportamiento permitido:

- `DeterministicPlannerStrategy` puede inspeccionar `AgentRequest` y producir un
  `PlannedAction` determinista.
- `LLMAssistedPlannerStrategy` puede construir input LLM estructurado, recibir
  output LLM bruto desde un proveedor de propuestas inyectado, validar ese
  output y hacer fallback al planner determinista cuando la validación falla.
- `LLMAssistedPlannerStrategy` puede convertir output validado en
  `PlannedAction(source="llm_assisted")`.
- Los registros de auditoría de augmentación LLM pueden guardar output bruto,
  output validado, estado de aceptación y motivo de fallback.

Comportamiento explícitamente prohibido:

- `LLM -> Tool`
- `LLM -> PolicyDecision`
- `LLM -> ToolRegistry`
- Las estrategias del planner no deben ejecutar tools.
- Las estrategias del planner no deben crear ni devolver `PolicyDecision`.
- Las estrategias del planner no deben registrar tools.
- Las estrategias del planner no deben saltarse `PolicyEngine`.

Validaciones necesarias para planificación asistida por LLM:

- JSON inválido se rechaza
- tools desconocidas se rechazan
- tools ausentes del `ToolRegistry` activo se rechazan
- payloads inválidos se rechazan
- outputs incompletos se rechazan
- output LLM rechazado activa fallback determinista

La autoridad sigue fuera del planner:

- `PolicyDecisionValue = ALLOW | DENY`
- `dry_run` es un flag de ejecución del runtime, no un `PolicyDecisionValue`
- las tools se ejecutan solo después de que `PolicyEngine` devuelva `ALLOW`

## Etiqueta de estado

- Planificación de producción: implementada
- Ejecución/integración LLM real: no implementada
- Frontera de planificación asistida por LLM: stub validado y desactivado salvo
  inyección explícita
