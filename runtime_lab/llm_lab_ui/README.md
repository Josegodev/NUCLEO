# llm_lab UI

## Proposito del modulo

`runtime_lab/llm_lab_ui` es una UI local de laboratorio para inspeccionar experimentos y artefactos del `llm_lab`.

No forma parte del runtime principal de NUCLEO.

Su objetivo actual es ofrecer una superficie local y acotada para:

- ejecutar experimentos del `llm_lab`;
- listar artefactos generados;
- inspeccionar el contenido de un artefacto;
- consultar el RAG documental mediante el backend lab-only.

## Frontera arquitectonica

Esta UI es lab-only.

Debe mantenerse fuera del flujo principal:

```text
Request -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> Tools
```

Limites explicitos:

- No ejecuta Tools.
- No pasa por AgentRuntime.
- No pasa por PolicyEngine.
- No modifica estado del runtime.
- No sustituye a AgentService.

## Superficie actual

El backend actual expone estos endpoints:

```text
GET  /
GET  /health
GET  /api/artifacts
GET  /api/artifacts/{experiment_id}
POST /api/experiments
POST /rag/search
POST /rag/answer
POST /rag/model-answer
```

Los endpoints RAG son lab-only. No pasan por el runtime principal.

## Estado RAG Docs

Existe una seccion frontend llamada `RAG Docs`.

Estado actual:

- Consume el backend lab-only mediante `POST /rag/answer`.
- Permite seleccionar modelos.
- Incluye opciones locales y externas.
- External providers are not enabled in this HARDENING step.
- `Run RAG` no llama proveedores externos.
- `POST /rag/search` existe en backend, pero la UI no lo usa todavia.
- `POST /rag/model-answer` existe como experimento lab-only.

Las opciones visuales actuales incluyen modelos locales como `llama3.1:8b`, `mistral` y `qwen`, ademas de opciones externas preparadas como `external/openai`, `external/anthropic` y `external/custom`.

Nota de contrato:

- El campo `model` se valida como parte del contrato frontend/backend.
- Actualmente `model` no se pasa a `build_answer()`.
- Por tanto, seleccionar `llama3.1:8b`, `mistral` o `qwen` todavia no cambia la generacion de respuesta.
- Los modelos externos siguen bloqueados.

## Estado RAG model-answer

`POST /rag/model-answer` es experimental y lab-only.

Flujo actual:

- Recupera evidencia documental con el RAG existente.
- Si no hay evidencia, devuelve `EVIDENCE_NOT_FOUND` y no llama al modelo.
- Si hay evidencia, envia al modelo local seleccionado la pregunta y la evidencia recuperada.
- La respuesta se marca con `Experimental model answer grounded on retrieved evidence. Not part of NUCLEO runtime.`

Limites:

- No forma parte del runtime principal.
- No ejecuta Tools.
- No llama proveedores externos.
- No introduce claves API.
- La salida del modelo sigue siendo no determinista.
- La evidencia recuperada sigue siendo la parte verificable.
- El modelo recibe evidencia recuperada, pero su respuesta no sustituye contratos del runtime ni documentacion canonica.

## Estado de integracion

El RAG CLI existe bajo:

```text
runtime_lab/llm_lab/rag_nucleo_docs/
```

Estado actual de integracion:

- La UI consume ese RAG a traves del backend lab-only.
- El backend expone RAG mediante `POST /rag/search`, `POST /rag/answer` y `POST /rag/model-answer`.
- La UI consume backend lab-only, no runtime.
- Cualquier futura ampliacion debe hacerse mediante contrato HTTP explicito y validado.

## Reglas HARDENING

Prohibiciones para esta zona:

- No conectar esta UI al runtime principal.
- No anadir proveedores externos sin validacion explicita.
- No introducir claves API en frontend.
- No convertir RAG en Tool.
- No duplicar logica RAG en frontend.

## Comandos utiles

Desde la raiz del repositorio:

```bash
python3 -m uvicorn runtime_lab.llm_lab_ui.backend.main:app --host 127.0.0.1 --port 8765
```

Si se usa el entorno virtual local del repositorio:

```bash
.venv/bin/python -m uvicorn runtime_lab.llm_lab_ui.backend.main:app --host 127.0.0.1 --port 8765
```

Ejemplo de consulta RAG local:

```bash
curl -s -X POST http://127.0.0.1:8765/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"Que hace dry_run=True?","top_k":5,"model":"llama3.1:8b"}'
```

Ejemplo de rechazo de proveedor externo:

```bash
curl -s -X POST http://127.0.0.1:8765/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"Que hace dry_run=True?","top_k":5,"model":"external/openai"}'
```

Ejemplo experimental con modelo local y evidencia RAG:

```bash
curl -s -X POST http://127.0.0.1:8765/rag/model-answer \
  -H 'Content-Type: application/json' \
  -d '{"query":"Que hace dry_run=True?","top_k":5,"model":"mistral"}'
```

## Criterio de aceptacion

- Archivo creado.
- La documentacion deja claro que `llm_lab_ui` es lab-only.
- RAG queda documentado como integracion lab-only, no runtime.
- `rag/model-answer` queda documentado como experimental y no determinista.
