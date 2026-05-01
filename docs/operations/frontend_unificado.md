# Frontend Unificado NUCLEO_AUGMENTED_CONTROLLED

## Estado actual entendido

`runtime_lab/llm_lab_ui/frontend/index.html` contiene un frontend unico con tres
modos de observacion:

- `HARDENING`
- `LLM_LAB`
- `COMPARE`

El frontend actua como visor HTTP. Esto significa que construye requests,
llama a endpoints existentes y renderiza respuestas completas. No decide
politica, no ejecuta tools y no reemplaza al runtime de NUCLEO.

Clasificacion: INFORMATIVO.

## Arquitectura

Flujo operacional actual:

```text
Frontend NUCLEO_AUGMENTED_CONTROLLED
  -> HTTP
  -> NUCLEO API /agent/run
  -> AgentService
  -> Runtime/orchestrator
  -> Planner
  -> PolicyEngine
  -> ToolRegistry
  -> Tool o dry_run
```

Flujo experimental de laboratorio:

```text
Frontend NUCLEO_AUGMENTED_CONTROLLED
  -> HTTP
  -> LLM_LAB API /rag/model-answer
  -> rag_nucleo_docs search
  -> evidence package
  -> local model adapter
  -> grounded answer
```

La separacion importante es esta:

```text
Frontend -> HTTP -> NUCLEO / LLM_LAB
```

El frontend no es un gateway de ejecucion. Un gateway es una capa que recibe una
peticion y decide a que servicio real delegarla. Aqui no se ha creado esa capa:
la UI llama explicitamente a cada backend segun el modo seleccionado.

Clasificacion: CRITICO.

## Modos

### HARDENING

Llama a NUCLEO:

```text
POST /agent/run
```

Uso previsto:

- observar el contrato real de `AgentResponse`
- probar `dry_run`
- comprobar trazabilidad minima mediante `trace_id`
- ver errores estructurados del runtime

### LLM_LAB

Llama al backend experimental:

```text
POST /rag/model-answer
```

Uso previsto:

- preguntar sobre documentacion indexada
- recuperar evidencia
- pedir una respuesta de modelo local basada solo en esa evidencia

### COMPARE

Ejecuta en paralelo:

```text
POST <NUCLEO base URL>/agent/run
POST <LLM_LAB base URL>/rag/model-answer
```

Los resultados se muestran en paneles separados. El frontend no mezcla las
respuestas ni decide cual es correcta.

Clasificacion: INFORMATIVO.

## Invariantes

Estos invariantes son reglas que no deberian romperse durante HARDENING. Un
invariante es una condicion que debe seguir siendo verdadera aunque cambie el
codigo alrededor.

- El frontend no ejecuta tools.
- El frontend no decide policy.
- El frontend no interpreta `ALLOW` ni `DENY`.
- El frontend no llama directamente a `PolicyEngine`.
- El frontend no llama directamente a `ToolRegistry`.
- El frontend no registra tools.
- El frontend no convierte una respuesta experimental de LLM_LAB en una accion
  de runtime.
- `COMPARE` no autoriza, no rechaza y no fusiona decisiones.

Clasificacion: CRITICO.

## Contratos reales de endpoints

### NUCLEO `POST /agent/run`

Contrato de request detectado en `AgentRequest`:

```json
{
  "input": "system info",
  "dry_run": true
}
```

Notas de contrato:

- `input` es alias aceptado para `user_input`.
- `dry_run` es booleano.
- `context` existe como objeto opcional.
- `options` existe para el modo de consola/propuesta.
- `extra="forbid"` esta activo en `AgentRequest`, por lo que campos fuera del
  contrato pueden ser rechazados.
- La autorizacion HTTP usa `Authorization: Bearer <api_key>`.

Contrato de respuesta publica:

```json
{
  "status": "success | error | rejected",
  "result": {},
  "errors": [],
  "trace_id": "string",
  "version": "execution_result.v1"
}
```

Notas de respuesta:

- `trace_id` es parte del contrato publico.
- `request_id` no esta garantizado como campo top-level.
- Si `status` no es `success`, debe existir al menos un error estructurado.
- El runtime decide si una tool se ejecuta o queda en `dry_run`.

Clasificacion: CRITICO.

### LLM_LAB `POST /rag/model-answer`

Contrato de request detectado en `RagModelAnswerRequest`:

```json
{
  "query": "Que hace dry_run=True?",
  "top_k": 5,
  "model": "llama3.1:8b"
}
```

Notas de contrato:

- `query` es obligatorio y no puede estar vacio.
- `top_k` debe estar entre `1` y `20`.
- `model` es obligatorio para `/rag/model-answer`.
- Modelos locales permitidos: `llama3.1:8b`, `mistral`, `qwen`.
- Modelos externos como `external/openai` responden
  `EXTERNAL_MODEL_NOT_ENABLED`.

Contrato de respuesta observado:

```json
{
  "status": "MODEL_ANSWER_READY",
  "query": "string",
  "model": "string",
  "answer": "string",
  "evidence": [],
  "warning": "string"
}
```

Si no hay evidencia recuperable, el backend puede responder:

```json
{
  "status": "EVIDENCE_NOT_FOUND",
  "query": "string",
  "model": "string",
  "answer": "",
  "evidence": []
}
```

Si hay evidencia pero el modelo considera que no contiene respuesta suficiente,
el prompt le exige responder exactamente:

```text
NO_EVIDENCE_FOR_ANSWER
```

Ese texto es una respuesta del modelo, no un `status` HTTP ni un estado
estructurado del backend.

Clasificacion: CRITICO.

## Limitaciones

### Provider no soportado

`provider` existe como control visual en el frontend, pero no es campo
contractual de `/rag/model-answer`.

En la UI actual, seleccionar `openai` se traduce a:

```json
{
  "model": "external/openai"
}
```

El backend rechaza ese modelo con:

```text
400 EXTERNAL_MODEL_NOT_ENABLED
```

Clasificacion: INFORMATIVO.

### `use_rag` no contractual

`use_rag` aparece en la UI como informacion de modo, pero el endpoint real ya
es RAG por definicion. No existe en este contrato HTTP un modo equivalente a:

```json
{
  "use_rag": false
}
```

Por eso el frontend no debe depender de `use_rag` como campo backend.

Clasificacion: INFORMATIVO.

### Sin normalizacion entre backends

NUCLEO y LLM_LAB devuelven formas distintas. El frontend las muestra, pero no
las transforma en un contrato comun.

Clasificacion: INFORMATIVO.

## Flujo de errores

### HTTP errors

Ocurren cuando el backend responde con codigo no exitoso o cuando la red falla.

Ejemplos:

- `400 EXTERNAL_MODEL_NOT_ENABLED`
- `401` o `403` si la API key de NUCLEO no es valida
- `422` si FastAPI rechaza el payload
- `502 MODEL_CALL_FAILED`
- `503 RAG_INDEX_NOT_FOUND`
- `network_error` si el backend no esta levantado o el puerto no responde

Resultado esperado en frontend:

- se conserva el `http_status`
- se muestra el cuerpo bruto si existe
- no se interpreta la decision de negocio

Clasificacion: CRITICO.

### Contract errors

Ocurren cuando el payload no cumple el contrato esperado por el endpoint.

Ejemplos:

- `query` vacio en `/rag/model-answer`
- `top_k` fuera del rango `1..20`
- `model` no soportado
- campos extra en `/agent/run`, porque `AgentRequest` usa `extra="forbid"`

Resultado esperado en frontend:

- se muestra el error del backend
- no se corrige silenciosamente el payload
- no se inventan campos de respuesta

Clasificacion: CRITICO.

### Parse errors

Ocurren cuando la respuesta HTTP no es JSON valido.

Resultado esperado en frontend:

- se conserva `response_raw`
- se informa `parse_error`
- se evita tratar la respuesta como contrato valido

Clasificacion: MEDIO.

## Cambio minimo recomendado

Mantener esta documentacion como contrato operacional del frontend unificado y
actualizarla solo cuando cambien endpoints, payloads, estados o limites reales.

No se recomienda crear nuevas capas, nuevos endpoints ni una normalizacion
global durante esta fase. Eso seria expansion de arquitectura.

Clasificacion: INFORMATIVO.

## Como comprobar si ha quedado bien

1. Levantar NUCLEO API:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

2. Levantar LLM_LAB UI/API con FastAPI:

```bash
.venv/bin/python -m uvicorn runtime_lab.llm_lab_ui.backend.main:app --host 127.0.0.1 --port 8765
```

3. Abrir:

```text
http://127.0.0.1:8765/
```

4. Validar que:

- `HARDENING` muestra respuesta de `/agent/run`.
- `LLM_LAB` muestra respuesta de `/rag/model-answer`.
- `COMPARE` muestra ambos resultados en paneles separados.
- Los errores se muestran como informacion auditable, no como decisiones del
  frontend.

## Riesgos o dudas pendientes

- CRITICO: si en el futuro el frontend empieza a interpretar policy, se rompe
  la frontera de responsabilidades.
- MEDIO: el RAG puede ser demasiado restrictivo y devolver
  `NO_EVIDENCE_FOR_ANSWER` aunque haya evidencia parcial.
- MEDIO: el ranking de evidencia puede mejorar, pero debe hacerse sin mezclarlo
  con runtime.
- INFORMATIVO: provider externo esta modelado como posibilidad visual, pero no
  esta habilitado por contrato backend.
