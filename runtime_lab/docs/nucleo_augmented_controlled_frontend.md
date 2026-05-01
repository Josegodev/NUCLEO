# NUCLEO Augmented Controlled Frontend

## Estado actual entendido

Este incremento crea un unico frontend de visualizacion para tres modos:

- `HARDENING`: llama al runtime determinista de NUCLEO.
- `LLM_LAB`: llama al backend experimental de `runtime_lab/llm_lab_ui`.
- `COMPARE`: llama a ambos backends en paralelo y muestra los resultados por separado.

Los backends permanecen separados. No se crea gateway, no se mezcla logica de
runtime con laboratorio y el frontend no accede a `PolicyEngine`,
`ToolRegistry` ni `Tools`.

## Endpoints usados

### HARDENING

```text
POST /agent/run
```

Payload enviado por el frontend:

```json
{
  "input": "string",
  "dry_run": true
}
```

Headers enviados:

```text
Authorization: Bearer <api_key>
Content-Type: application/json
```

### LLM_LAB

```text
POST /rag/model-answer
```

Payload real enviado por el frontend:

```json
{
  "query": "string",
  "top_k": 5,
  "model": "llama3.1:8b"
}
```

### COMPARE

El modo `COMPARE` ejecuta en paralelo:

- `POST <NUCLEO base URL>/agent/run`
- `POST <LLM_LAB base URL>/rag/model-answer`

Los resultados se renderizan en paneles separados. Un fallo en un panel no
bloquea el otro.

## Contratos reales detectados

### NUCLEO `/agent/run`

El schema real es `AgentRequest`.

Campos relevantes:

- `input` es alias valido de `user_input`.
- `dry_run` es booleano.
- `extra="forbid"`, por lo que campos no definidos son rechazados.

La respuesta real es `AgentResponse`.

Campos top-level:

- `status`
- `result`
- `errors`
- `trace_id`
- `version`

`request_id` no esta garantizado en la respuesta publica. El frontend lo busca
si existe, pero no lo inventa.

### LLM_LAB `/rag/model-answer`

El schema real es `RagModelAnswerRequest`.

Campos aceptados:

- `query`
- `top_k`
- `model`

Diferencias frente al contrato esperado:

- No existe campo backend `provider`.
- No existe campo backend `use_rag`.
- El endpoint es RAG por contrato; no hay modo HTTP equivalente a
  `use_rag=false`.
- `openai` no esta habilitado en este endpoint. El backend reconoce modelos
  externos como deshabilitados y responde error.

Respuesta observada por codigo:

- `status`
- `query`
- `model`
- `answer`
- `evidence`
- `warning`

No hay campos garantizados `fallback_used` ni `fallback_reason`. El frontend los
muestra solo si aparecen.

## Decisiones tomadas

- CRITICO: el frontend no interpreta `ALLOW` ni `DENY`; solo muestra la
  respuesta backend completa.
- CRITICO: `dry_run` se envia a NUCLEO y lo decide el runtime. No se simula en
  frontend.
- CRITICO: `LLM_LAB` no llama a `/agent/run` ni ejecuta tools de NUCLEO.
- CRITICO: `COMPARE` mantiene respuestas aisladas y no decide cual es mejor.
- INFORMATIVO: la configuracion global se persiste en `localStorage` para uso
  local.
- INFORMATIVO: `provider` queda como control visual, pero no se envia como
  campo porque el contrato real no lo acepta.
- INFORMATIVO: `use_rag` aparece fijo en `true` porque el endpoint real es RAG.

## Limitaciones actuales

- No hay gateway ni normalizacion de respuestas entre backends.
- No hay endpoint LLM_LAB para respuesta directa sin RAG.
- `provider=openai` no esta habilitado en el backend actual de LLM_LAB.
- El frontend no descubre contratos dinamicamente; usa los contratos detectados
  en codigo.
- El frontend no guarda historico de ejecuciones.
- El smoke test de `rag_nucleo_docs` ya carga y ejecuta, pero la suite completa
  aun falla por expectativas de contenido/ranking del indice, no por error de
  importacion ni por contrato minimo `doc_id`, `score`, `snippet`.

## Validacion realizada

- `POST /agent/run` con `{ "input": "system info", "dry_run": true }` responde
  `status=success`, `dry_run=true`, `executed=false` y `trace_id`.
- `POST /rag/search` responde `status=FOUND` con resultados que incluyen
  `doc_id`, `score` y `snippet`.
- `POST /rag/model-answer` responde `status=MODEL_ANSWER_READY` con `answer` y
  `evidence` cuando el modelo local esta disponible.
- `POST /rag/model-answer` con `model=external/openai` responde
  `400 EXTERNAL_MODEL_NOT_ENABLED`.
- `python3 -m pytest tests/test_runtime_tracing.py::RuntimeTracingTests::test_agent_run_endpoint_contract_for_valid_dry_run`
  pasa.

## Siguientes pasos

- PREMATURO: crear un gateway. Puede tener sentido mas adelante si se quiere
  una sola API publica, pero ahora aumentaria arquitectura sin necesidad.
- INFORMATIVO: anadir endpoint LLM_LAB explicito para `use_rag=false`, solo si
  el laboratorio necesita comparar respuesta directa contra RAG.
- INFORMATIVO: exponer un endpoint de metadata de contratos para que el frontend
  pueda mostrar capacidades reales sin duplicarlas.
- CRITICO: mantener la regla de aislamiento: cualquier ejecucion de tools debe
  seguir entrando por `Request -> Planner -> PolicyEngine -> ToolRegistry ->
  Tool -> Response`.
