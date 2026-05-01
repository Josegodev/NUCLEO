# llm_lab UI

This UI is not part of the NUCLEO execution pipeline and must not be used as an entry point for agent execution.

## Proposito del modulo

`runtime_lab/llm_lab_ui` es una UI local de laboratorio para inspeccionar experimentos y artefactos del `llm_lab`.

No forma parte del runtime principal de NUCLEO.

Su objetivo actual es ofrecer una superficie local y acotada para:

- ejecutar experimentos del `llm_lab`;
- listar artefactos generados;
- inspeccionar el contenido de un artefacto;
- preparar visualmente una futura seccion RAG Docs sin conectarla todavia.

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
```

No hay endpoints RAG expuestos en esta iteracion.

## Estado RAG Docs

Existe una seccion frontend llamada `RAG Docs`.

Estado actual:

- Es UI-only.
- Permite seleccionar modelos visualmente.
- Incluye opciones locales y externas.
- External providers are not enabled in this HARDENING step.
- `Run RAG` no llama backend.
- No existen todavia `POST /rag/search` ni `POST /rag/answer`.

Las opciones visuales actuales incluyen modelos locales como `llama3.1:8b`, `mistral` y `qwen`, ademas de opciones externas preparadas como `external/openai`, `external/anthropic` y `external/custom`.

## Estado de integracion

El RAG CLI existe bajo:

```text
runtime_lab/llm_lab/rag_nucleo_docs/
```

Estado actual de integracion:

- La UI todavia no consume ese RAG.
- El backend todavia no expone RAG.
- Cualquier futura conexion debe hacerse mediante contrato HTTP explicito y validado.

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

## Criterio de aceptacion

- Archivo creado.
- No hay cambios de codigo para esta documentacion.
- La documentacion deja claro que `llm_lab_ui` es lab-only.

##
For full interaction details see:
runtime_lab/docs/llm_lab_ui_interaction.md
model is validated as API contract metadata but is not yet used for answer generation.