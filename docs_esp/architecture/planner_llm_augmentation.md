> Archivo origen: `docs/architecture/planner_llm_augmentation.md`
> Ultima sincronizacion: `2026-05-01`

# Augmentacion LLM Controlada En Planner

## Estado actual

La ruta de produccion de NUCLEO sigue siendo:

```text
API -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> Tool -> AgentResponse
```

Contratos de seguridad actuales:

- `Planner` devuelve un `PlannedAction` tipado.
- `PolicyEngine` mantiene la autoridad para permitir o denegar.
- `ToolRegistry` mantiene la autoridad sobre las tools registradas.
- `dry_run=True` nunca llama a `tool.run(...)`.
- `runtime_lab/llm_lab/` sigue aislado del runtime de produccion.

Este cambio introduce una frontera de augmentacion solo dentro de Planner. No
conecta ningun proveedor LLM al runtime de produccion.

## Riesgos de introducir LLM

Una salida LLM es probabilistica. Eso significa que no debe tratarse como verdad
de runtime.

Riesgos principales:

- Texto libre podria confundirse con un plan ejecutable.
- El modelo podria mencionar una tool desconocida o no registrada.
- El modelo podria producir un payload que no cumple el contrato de la tool.
- El modelo podria parecer que se salta `PolicyEngine` si se ejecuta directamente.
- Se perderia auditoria si no se registra input bruto y output bruto.

La mitigacion es separar responsabilidades: el LLM solo propone. Planner valida
la propuesta. Runtime sigue pasando el `PlannedAction` por `PolicyEngine`,
`ToolRegistry` y validacion de input de tool.

## Diseno de PlannerStrategy

`PlannerStrategy` es la interfaz explicita de planificacion:

```text
AgentRequest -> PlannerStrategy.create_plan(...) -> PlannedAction
```

Estrategias implementadas:

- `DeterministicPlannerStrategy`: comportamiento actual basado en reglas.
- `LLMAssistedPlannerStrategy`: stub futuro para propuestas asistidas por LLM.

El comportamiento por defecto sigue siendo determinista porque `Planner()` usa
`DeterministicPlannerStrategy` salvo que se inyecte otra estrategia
explicitamente.

`LLMAssistedPlannerStrategy` no llama a un LLM real. Acepta un callback opcional
de propuesta para pruebas o integracion futura. Si esta desactivado, ausente o
falla, cae automaticamente al planner determinista.

## Contrato de entrada

La entrada al LLM debe ser siempre estructurada:

```json
{
  "goal": "str",
  "context": ["str"],
  "constraints": ["str"]
}
```

Las restricciones deben dejar claro que el LLM:

- devuelve solo JSON
- solo propone tools
- nunca ejecuta tools
- solo usa tools registradas
- no puede modificar `ToolRegistry`
- no puede saltarse `PolicyEngine`

## Contrato de salida

La salida del LLM debe ser JSON valido:

```json
{
  "proposed_plan": [
    {
      "tool_name": "echo",
      "payload": {
        "text": "hola"
      }
    }
  ],
  "justification": "echo was requested",
  "confidence": 0.91
}
```

El texto libre es invalido. Los campos extra de nivel superior son invalidos.
Los campos extra dentro de cada step son invalidos.

El runtime actual soporta exactamente un `PlannedAction`. Por eso los planes LLM
con multiples pasos se rechazan hasta que el contrato del runtime se amplie de
forma deliberada.

## Validaciones necesarias

`LLMPlanOutputValidator` rechaza:

- JSON invalido
- salida que no cumple `LLMPlanProposal`
- steps no parseables
- nombres de tool fuera del conjunto cerrado
- nombres de tool conocidos pero no presentes en el `ToolRegistry` activo
- payloads que no cumplen el contrato de la tool objetivo
- propuestas con multiples steps, porque el runtime actual acepta una sola accion

La salida aceptada se convierte en:

```text
PlannedAction(source="llm_assisted")
```

Esto sigue siendo solo una propuesta. No es autorizacion.

## Flujo actualizado

```text
API
  -> AgentService
  -> AgentRuntime
  -> Planner
       -> deterministic strategy
       -> optional llm_assisted strategy
            -> structured LLM input
            -> raw LLM output
            -> output validation
            -> fallback to deterministic strategy on failure
  -> PolicyEngine
  -> ToolRegistry
  -> Tool
  -> AgentResponse
```

Ninguna tool puede ejecutarse directamente desde la ruta LLM.

## Trazabilidad

`LLMAssistedPlannerStrategy` registra en memoria:

- input estructurado enviado a la frontera LLM
- output bruto devuelto por el proveedor de propuesta
- output validado cuando se acepta
- motivo de aceptacion o rechazo

La implementacion actual no persiste estos registros y no modifica las fases de
tracing del runtime.

## Ejemplo completo

Request:

```json
{
  "user_input": "say hola",
  "dry_run": true
}
```

Input LLM:

```json
{
  "goal": "say hola",
  "context": [],
  "constraints": [
    "Return valid JSON only.",
    "Propose tools only; never execute tools.",
    "Use registered tools only.",
    "PolicyEngine remains the final authority before execution.",
    "ToolRegistry must not be modified."
  ]
}
```

Output bruto LLM:

```json
{
  "proposed_plan": [
    {
      "tool_name": "echo",
      "payload": {
        "text": "hola"
      }
    }
  ],
  "justification": "echo was requested",
  "confidence": 0.91
}
```

Resultado de validacion:

```text
accepted=true
source=llm_assisted
tool_name=echo
payload={"text": "hola"}
```

Resultado de runtime con `dry_run=true`:

```text
PolicyEngine evalua primero.
ToolRegistry resuelve la tool.
El input de tool se valida.
tool.run(...) no se llama.
```

## Criterios de aceptacion

- El comportamiento determinista no cambia si `llm_assisted` esta desactivado.
- La salida LLM no puede ejecutar tools.
- La salida LLM no puede saltarse `PolicyEngine`.
- La salida LLM no puede modificar `ToolRegistry`.
- La salida LLM es auditable y rechazable antes de convertirse en `PlannedAction`.
