# Productive Agent Console v0

## Objetivo

Convertir la superficie visual de `runtime_lab/llm_lab_ui/frontend/` en una consola local para llamar al runtime productivo real de NUCLEO sin crear endpoints paralelos.

La consola v0 solo trabaja en modo:

- `agent_mode = proposal_only`
- `dry_run = true`

Esto significa que el usuario puede pedir una acción, el sistema puede proponer una tool, pero ninguna tool se ejecuta desde la consola.

## Arquitectura real

La arquitectura usada es la existente:

```text
Frontend
  -> POST /agent/run
  -> AgentService
  -> AgentRuntime
  -> Planner
  -> PolicyEngine
  -> ToolRegistry
  -> dry_run response
```

No se crea `/api/agent-chat` ni ningún endpoint equivalente.

## Flujo

El frontend envía:

```json
{
  "input": "mensaje usuario",
  "context": {},
  "options": {
    "backend": "auto",
    "model_id": "llama3.1:8b",
    "agent_mode": "proposal_only",
    "dry_run": true
  }
}
```

`AgentRequest` acepta `input` como alias de `user_input` y normaliza `options`. En `proposal_only`, `dry_run` queda forzado a `true`.

## Contratos

Contratos principales:

- `AgentRequest`: entrada HTTP del endpoint real.
- `PlannedAction`: salida del Planner consumida por Runtime.
- `PolicyDecision`: decisión cerrada de `PolicyEngine`.
- `ToolRegistry`: resolución de la tool propuesta.

La salida LLM aceptada por `planner_augmentation` es:

```json
{
  "intent": "intencion interpretada",
  "suggested_action": "echo",
  "arguments": {
    "text": "hola"
  },
  "confidence": 0.9
}
```

`suggested_action` debe corresponder a una tool conocida y registrada. `arguments` se valida con el contrato de payload de la tool.

## Seguridad

La consola no ejecuta tools.

El modelo no ejecuta tools.

El LLM solo puede proponer una acción estructurada. Después:

```text
Planner proposal -> PolicyEngine -> ToolRegistry -> dry_run skip
```

Aunque `PolicyEngine` devuelva `ALLOW`, `dry_run=true` evita `tool.run`.

## Approval Gate real

La consola v0 tiene dos pasos separados:

```text
proposal_only + dry_run=true -> PROPOSED
approve=true                -> APPROVED -> EXECUTED
approve=false               -> REJECTED
```

`proposal_only` no ejecuta. Solo produce una propuesta validada por el runtime y la persiste asociada a `trace_id`.

La persistencia guarda:

- `trace_id`
- `user_input`
- `planned_action`
- `proposed_tool`
- `arguments`
- `policy_decision_initial`
- `created_at`
- `execution_state = PROPOSED`

El endpoint de aprobación es:

```text
POST /agent/approve
```

Request:

```json
{
  "trace_id": "trace-...",
  "approved": true
}
```

Reglas del gate:

- `approve` no llama al LLM.
- `approve` no llama al Planner.
- `approve` no acepta `tool_name`.
- `approve` no acepta `payload`.
- `approve` recupera la proposal persistida por `trace_id`.
- `approve` reconstruye el `PlannedAction` persistido.
- `approve` vuelve a ejecutar `PolicyEngine`.
- Si `PolicyEngine` devuelve `DENY`, el estado pasa a `DENIED` y no se ejecuta nada.
- Si el payload no valida contra el contrato de la tool, el estado pasa a `ERROR` y no se ejecuta nada.
- Si todo valida, `ToolRegistry` resuelve la tool y solo entonces se llama `tool.run`.
- `reject` pasa a `REJECTED` y nunca ejecuta.

La idempotencia es crítica:

- Si una proposal ya está `EXECUTED`, una segunda aprobación devuelve el estado existente.
- Una segunda aprobación no vuelve a llamar `tool.run`.

Estados posibles:

```text
PROPOSED
APPROVED
EXECUTED
REJECTED
DENIED
ERROR
```

## Approval Gate

La aprobación real vive en `/agent/approve`. El gate queda representado por estas barreras:

- `PolicyEngine`: decide `ALLOW` o `DENY`.
- `dry_run=true`: bloquea ejecución durante la propuesta.
- `ApprovalStore`: exige que exista una proposal persistida por `trace_id`.
- `ToolRegistry`: resuelve de nuevo la tool antes de ejecutar.
- `tool.validate_input`: valida de nuevo el payload persistido antes de `tool.run`.

## Observabilidad

La respuesta dry-run incluye metadata mínima cuando hay augmentación:

- `proposal`
- `model_used`
- `backend_used`
- `latency_ms`
- `fallback_used`
- `fallback_reason`

El runtime mantiene `trace_id` en `AgentResponse`.

## Fallback local/OpenAI

`app/adapters/model_router.py` encapsula la selección de modelo:

- `local`: usa Ollama mediante `runtime_lab/llm_lab/model_adapter.py`.
- `openai`: usa OpenAI si `OPENAI_API_KEY` está configurada.
- `auto`: intenta local primero y cae a OpenAI si local falla.

El runtime productivo no llama directamente a `llm_lab`.

## Riesgos

- Si Ollama no está disponible y no existe `OPENAI_API_KEY`, la augmentación cae al planner determinista.
- Si el LLM devuelve JSON inválido, se rechaza la propuesta y se usa fallback determinista.
- Si el LLM propone una tool no registrada, se rechaza la propuesta.
- Si la documentación vieja no se actualiza, aparece drift sobre si `llm_lab_ui` es lab-only o consola productiva.

## GAP futuros

- Approval gate explícito para pasar de propuesta a ejecución.
- Historial de conversación persistente.
- Selector dinámico de modelos disponibles.
- Observabilidad de trazas desde UI.
- Gestión segura de credenciales fuera del frontend local.
