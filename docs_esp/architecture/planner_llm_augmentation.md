> Archivo origen: `docs/architecture/planner_llm_augmentation.md`
> Ultima sincronizacion: `2026-05-01`

# Augmentacion LLM Controlada En Planner

## Estado actual

NUCLEO tiene una frontera de augmentacion LLM controlada dentro del Planner. El
LLM puede proponer una accion estructurada, pero no puede autorizar, resolver ni
ejecutar una tool.

El orden de ejecucion de produccion sigue siendo:

```text
AgentRequest
-> AgentService
-> AgentRuntime
-> Planner
-> PolicyEngine
-> ToolRegistry
-> Tool o proposal dry-run
-> AgentResponse
```

Para Productive Agent Console v0, la request usa:

```json
{
  "options": {
    "agent_mode": "proposal_only",
    "dry_run": true
  }
}
```

`proposal_only` permite planificacion asistida por LLM. `dry_run=true` impide
`tool.run(...)`.

## Model Router

`app/adapters/model_router.py` es la frontera de modelo que ve el runtime.

Responsabilidades:

- seleccionar `local`, `openai` o `auto`
- llamar a Ollama local mediante `runtime_lab/llm_lab/model_adapter.py`
- llamar a OpenAI mediante la API HTTP de chat completions
- devolver un contrato normalizado unico

Resultado normalizado:

```json
{
  "output": "...",
  "model_used": "...",
  "backend_used": "...",
  "latency_ms": 123.0,
  "fallback_used": false,
  "fallback_reason": null
}
```

El runtime no llama directamente a `runtime_lab/llm_lab`. Llama a
`ModelRouterProposalProvider`, que llama a `ModelRouter`.

## Contrato del prompt

`ModelRouterProposalProvider` construye un prompt con:

- objetivo del usuario
- contexto estructurado
- restricciones fijas de seguridad
- catalogo activo de contratos de tools

El catalogo se genera mediante:

```text
build_tool_contract_prompt(tool_registry)
```

Esa funcion lee `tool_registry.list_contracts()` y renderiza los nombres de
tools registradas junto con los schemas exactos de argumentos. Esto evita
parches hardcodeados por tool, como `message -> text`.

Fragmento de catalogo:

```text
Available tools and required argument schemas:

- echo
  arguments:
    text: string

- system_info
  arguments:
    {}
```

Reglas enviadas al modelo:

- usar solo tools listadas
- usar nombres exactos de argumentos
- no inventar campos
- no usar aliases
- si no encaja ninguna tool, devolver `suggested_action=null` y `arguments={}`
- devolver solo JSON, opcionalmente envuelto en un fenced block `json`

## Contrato de salida

Forma aceptada de salida LLM:

```json
{
  "intent": "echo request",
  "suggested_action": "echo",
  "arguments": {
    "text": "hola"
  },
  "confidence": 0.9
}
```

`suggested_action` puede ser `null` solo cuando no debe planificarse ninguna
accion. En ese caso `arguments` debe ser `{}`.

El texto libre es invalido. Los campos extra de payload son invalidos porque los
payloads se validan contra el contrato Pydantic de la tool seleccionada.

## Normalizacion JSON

`_strip_json_fence(raw)` acepta solo:

- JSON puro
- un fenced block Markdown completo cuya apertura esta vacia o etiquetada como
  `json` y cuya ultima linea es un cierre de fence

El normalizador no extrae JSON desde texto narrativo. Estos casos son invalidos:

- texto antes o despues del JSON
- fence de apertura sin fence de cierre
- lenguajes de fence distintos de vacio o `json`

La cadena normalizada se pasa a `json.loads(...)`.

## Validacion

`LLMPlanOutputValidator` realiza las comprobaciones del lado runtime:

1. parsear JSON
2. validar campos requeridos
3. validar rango de `confidence`
4. aceptar `suggested_action=null` solo con argumentos vacios
5. validar el nombre de tool contra el conjunto cerrado
6. verificar que la tool existe en el `ToolRegistry` activo
7. validar `arguments` con el schema de payload de la tool
8. convertir la proposal aceptada en `PlannedAction(source="llm_assisted")`

La proposal aceptada sigue sin ser autorizacion. Runtime pasa el
`PlannedAction` por `PolicyEngine`, luego por `ToolRegistry` y luego por
validacion de payload antes de dry-run o ejecucion.

## Fallback

`LLMAssistedPlannerStrategy` cae al planner determinista cuando:

- falla el backend de modelo seleccionado
- el output del modelo esta vacio
- falla la normalizacion o el parseo JSON
- la forma de la proposal es invalida
- la tool es desconocida o no registrada
- el payload no cumple el contrato de la tool seleccionada

La metadata de fallback se adjunta al plan resultante cuando esta disponible:

- `augmentation_attempted`
- `backend`
- `model_id`
- `backend_used`
- `model_used`
- `latency_ms`
- `fallback_used`
- `fallback_reason`

Si la planificacion determinista tambien devuelve `no_plan`, la respuesta puede
ser `rejected`, pero conserva metadata que demuestra que se intento la
augmentacion.

## Frontera de aprobacion

La augmentacion del Planner termina en una proposal. La ejecucion real queda
controlada por el Approval Gate:

```text
PROPOSED -> APPROVED -> EXECUTED
PROPOSED -> REJECTED
```

`POST /agent/approve` no llama a `ModelRouter`, no llama a
`planner_augmentation` y no llama al Planner. Carga la proposal persistida por
`trace_id`, revalida `PolicyEngine`, resuelve otra vez `ToolRegistry`, valida el
payload persistido y solo entonces llama a `tool.run(...)`.

## Invariantes

- La salida LLM nunca se ejecuta directamente.
- La salida LLM nunca crea un `PolicyDecision`.
- La salida LLM nunca muta `ToolRegistry`.
- El frontend no puede editar payloads ejecutables durante aprobación.
- `PolicyDecisionValue` sigue siendo `ALLOW | DENY`.
- `dry_run` sigue siendo un flag de ejecución del runtime.
- La planificación multi-step no está implementada.
- La memoria conversacional no está implementada.
