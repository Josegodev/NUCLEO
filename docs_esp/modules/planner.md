> Archivo origen: `docs/modules/planner.md`
> Última sincronización: `2026-05-01`

# Planner

## Capa

Arquitectura verificada

## Propósito

Transformar un `AgentRequest` en una acción candidata.

El planner propone. No autoriza, no resuelve la verdad de runtime y no ejecuta.

## Comportamiento actual verificado

La estrategia determinista del planner actualmente:

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

### LLM Augmentation

La augmentación LLM controlada se activa solo cuando:

```text
request.options.agent_mode == "proposal_only"
```

El `Planner` de producción está configurado con
`LLMAssistedPlannerStrategy`. Esa estrategia pide salida a un proveedor de
propuestas solo en `proposal_only`. Para el resto de requests usa fallback
determinista.

El flujo de salida LLM es:

```text
raw model output
-> _strip_json_fence(...)
-> json.loads(...)
-> validación de forma AgentActionProposal
-> lookup de tool en ToolRegistry
-> validación de payload de tool
-> PlannedAction(source="llm_assisted")
```

Los formatos aceptados son deliberadamente estrechos:

- JSON puro
- JSON envuelto en un fenced block Markdown cuya apertura está vacía o
  etiquetada como `json`

Texto libre mezclado con JSON es inválido. Un fenced block sin cierre es
inválido. El código no extrae JSON desde texto narrativo.

Forma esperada:

```json
{
  "intent": "string",
  "suggested_action": "echo",
  "arguments": {
    "text": "hola"
  },
  "confidence": 0.9
}
```

`suggested_action` puede ser `null` si no encaja ninguna tool listada. En ese
caso, `arguments` debe ser `{}` y el resultado se convierte en `no_plan`.

#### Inyección de contratos de tools

`build_tool_contract_prompt(tool_registry)` construye el catálogo del prompt
desde el `ToolRegistry` activo:

```text
Available tools and required argument schemas:

- echo
  arguments:
    text: string

- system_info
  arguments:
    {}
```

El catálogo se genera desde `tool_registry.list_contracts()`. No está
hardcodeado por tool.

Reglas entregadas al modelo:

- usar solo tools listadas
- usar nombres exactos de argumentos
- no inventar campos
- no usar aliases
- si no encaja ninguna tool, devolver `suggested_action=null` y `arguments={}`
- devolver solo JSON, opcionalmente envuelto en un fenced block `json`

Después del parseo, la validación del runtime sigue aplicando el mismo contrato.
Por ejemplo, `{"message": "hola"}` es inválido para `echo`; el campo aceptado es
`text`.

#### Fallback

La estrategia cae al planner determinista cuando:

- falla el proveedor de modelo
- falla la normalización JSON
- falla el parseo JSON
- la forma de la proposal es inválida
- la tool es desconocida o no está registrada
- el payload no cumple el contrato de la tool seleccionada

El plan de fallback transporta metadata como `augmentation_attempted`,
`fallback_used` y `fallback_reason` cuando está disponible.

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
- Planificación determinista: implementada
- Planificación asistida por LLM controlada: implementada para `proposal_only`
- Ejecución de tools por LLM: no implementada y explícitamente prohibida
