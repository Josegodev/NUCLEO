# NUCLEO Augmented Controlled Frontend

`runtime_lab/llm_lab_ui/frontend/` contiene un frontend unico para visualizar
tres modos sin mezclar backends:

- `HARDENING`: llama a NUCLEO API.
- `LLM_LAB`: llama a la API experimental de `llm_lab`.
- `COMPARE`: llama a ambos en paralelo y muestra las respuestas por separado.

Endpoint productivo usado por `HARDENING`:

```text
POST /agent/run
```

Endpoint experimental usado por `LLM_LAB`:

```text
POST /rag/model-answer
```

No crea gateway. La UI solo envia requests HTTP y renderiza respuestas.

## Frontera arquitectonica

Flujo real de NUCLEO:

```text
Frontend -> /agent/run -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> dry_run response
```

Limites explicitos:

- No ejecuta tools desde frontend.
- No permite que el LLM ejecute tools.
- No bypass de `PolicyEngine`.
- No crea endpoints tipo `/api/agent-chat`.
- No acopla contratos entre HARDENING y LLM_LAB.
- `dry_run` lo controla el runtime.

## Comandos utiles

Terminal 1, NUCLEO API:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2, LLM_LAB API + frontend:

```bash
python3 -m uvicorn runtime_lab.llm_lab_ui.backend.main:app --host 127.0.0.1 --port 8765
```

Si se usa el entorno virtual local del repositorio:

```bash
.venv/bin/python -m uvicorn runtime_lab.llm_lab_ui.backend.main:app --host 127.0.0.1 --port 8765
```

Abrir:

```text
http://127.0.0.1:8765/
```

## Como levantar correctamente

Este UI debe levantarse con `uvicorn` apuntando al backend FastAPI:

```bash
.venv/bin/python -m uvicorn runtime_lab.llm_lab_ui.backend.main:app --host 127.0.0.1 --port 8765
```

No usar:

```bash
python3 -m http.server
```

`http.server` solo sirve archivos estaticos. Puede mostrar `index.html`, pero
no registra endpoints FastAPI como:

```text
POST /rag/model-answer
```

Si el puerto `8765` esta ocupado, cerrar el proceso anterior o usar otro puerto
y actualizar `LLM_LAB base URL` en la UI.

## Frontend estatico vs backend FastAPI

El frontend estatico es:

```text
runtime_lab/llm_lab_ui/frontend/index.html
```

Responsabilidad:

- mostrar tabs `HARDENING`, `LLM_LAB` y `COMPARE`
- construir payloads HTTP
- llamar a los backends
- renderizar respuestas y errores

El backend FastAPI es:

```text
runtime_lab/llm_lab_ui/backend/main.py
```

Responsabilidad:

- servir `/`
- exponer `/health`
- exponer endpoints de laboratorio como `/rag/model-answer`
- llamar al modulo RAG experimental de `runtime_lab/llm_lab`

El frontend no ejecuta tools, no decide policy y no interpreta `ALLOW`/`DENY`.

## Ejemplo valido de `/rag/model-answer`

Con el backend levantado en `127.0.0.1:8765`:

```bash
curl -sS -X POST http://127.0.0.1:8765/rag/model-answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"Que hace dry_run=True?","top_k":5,"model":"llama3.1:8b"}'
```

Payload contractual:

```json
{
  "query": "Que hace dry_run=True?",
  "top_k": 5,
  "model": "llama3.1:8b"
}
```

Campos como `provider` y `use_rag` no forman parte del contrato de este
endpoint. `provider=openai` en la UI se traduce a `external/openai`, que el
backend actual rechaza con `EXTERNAL_MODEL_NOT_ENABLED`.

## Estados de respuesta RAG con modelo

### `MODEL_ANSWER_READY`

Significa que el backend:

- encontro evidencia recuperable
- llamo al modelo configurado
- devolvio una respuesta en `answer`
- incluyo la evidencia usada en `evidence`

No significa que la respuesta sea una decision de runtime. Sigue siendo una
respuesta experimental de LLM_LAB.

### `NO_EVIDENCE`

Significa que `rag_nucleo_docs/search.py` no recupero evidencia para la
pregunta. En este caso el backend no llama a LM Studio.

Respuesta esperada:

```json
{
  "status": "NO_EVIDENCE",
  "answer": "NO_EVIDENCE_FOR_ANSWER",
  "evidence": [],
  "fallback_used": false,
  "fallback_reason": null
}
```

### `MODEL_ERROR`

Significa que habia evidencia, pero la llamada a LM Studio fallo o devolvio una
respuesta no utilizable. El backend mantiene la evidencia recuperada y devuelve
error controlado en JSON estable.

Respuesta esperada:

```json
{
  "status": "MODEL_ERROR",
  "answer": "",
  "evidence": ["..."],
  "fallback_used": true,
  "fallback_reason": "connection_error: LM Studio is not reachable"
}
```

### `NO_EVIDENCE_FOR_ANSWER`

`NO_EVIDENCE_FOR_ANSWER` no es un `status` estructurado del endpoint. Es el
texto exacto que el prompt exige al modelo cuando la evidencia recuperada no
contiene suficiente informacion para responder.

Puede ocurrir incluso si `evidence` tiene elementos, porque la politica del
prompt es estricta: el modelo debe responder solo con evidencia y no inventar.

Regla enviada al modelo:

```text
Responde SOLO usando la evidencia proporcionada. Si la evidencia no contiene la respuesta, responde NO_EVIDENCE_FOR_ANSWER.
```

## Prueba manual de `/rag/model-answer`

Con LM Studio apagado, si hay evidencia, debe devolver `MODEL_ERROR` controlado:

```bash
curl -i -X POST http://127.0.0.1:8765/rag/model-answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"Que hace el Planner?","top_k":5,"model":"qwen"}'
```

Para verificar que no llama al modelo sin evidencia:

```bash
curl -i -X POST http://127.0.0.1:8765/rag/model-answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"zzzz_no_deberia_tener_evidencia_12345","top_k":5,"model":"qwen"}'
```

Con LM Studio encendido en su API OpenAI-compatible local, el mismo endpoint
debe devolver `MODEL_ANSWER_READY` cuando el modelo cargado responda.

## Criterio de aceptacion

- `HARDENING` llama a `POST /agent/run`.
- `LLM_LAB` llama a `POST /rag/model-answer`.
- `COMPARE` ejecuta ambos en paralelo.
- Las respuestas completas y errores quedan visibles.
- El frontend no decide policy ni ejecuta tools.

Para el contrato y decisiones de este incremento, ver:

```text
runtime_lab/docs/nucleo_augmented_controlled_frontend.md
```
