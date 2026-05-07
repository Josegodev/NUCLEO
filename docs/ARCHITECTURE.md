# NUCLEO Architecture Snapshot

Fecha: 2026-05-02

Este documento resume la arquitectura actual para orientar el refactor
incremental. No sustituye todavia a todos los documentos historicos; sirve como
snapshot compacto para nuevos cambios.

## 1. Estado actual entendido

NUCLEO ejecuta peticiones de agente mediante un pipeline controlado:

```text
AgentRequest
-> API
-> AgentService
-> AgentRuntime
-> Planner
-> PolicyEngine
-> ToolRegistry
-> Tool o proposal/dry_run
-> AgentResponse
```

El objetivo del diseno actual es que ningun modelo, frontend o laboratorio
ejecute una tool directamente. La ejecucion real pasa por runtime, policy,
registry y validacion de payload.

Clasificacion: CRITICO.

## 2. Problema detectado

La arquitectura esta razonablemente separada en el core, pero el repositorio ha
crecido con laboratorios, documentacion duplicada y adaptadores historicos. Eso
crea ruido para leer el sistema.

Puntos de entrada principales:

- `app.main:app`: API FastAPI productiva.
- `runtime_lab.llm_lab.nucleo_rag_api:app`: API experimental de evidencia RAG.
- `runtime_lab.llm_lab_ui.backend.main:app`: UI/API experimental de laboratorio.
- Scripts bajo `runtime_lab/document_loader/` y `runtime_lab/llm_lab/`.

## 3. Impacto tecnico

Los limites criticos son estos:

| Limite | Contrato |
| --- | --- |
| API -> AgentService | La ruta HTTP no decide negocio; delega. |
| AgentService -> AgentRuntime | Servicio fino; no planifica, no autoriza, no ejecuta. |
| AgentRuntime -> Planner | Planner debe devolver `PlannedAction`. |
| AgentRuntime -> PolicyEngine | Policy debe devolver `PolicyDecision`. |
| PolicyEngine -> ToolRegistry | Policy puede comprobar si la tool esta registrada, pero no ejecuta. |
| AgentRuntime -> ToolRegistry | Runtime resuelve la tool despues de policy allow. |
| Tool -> AgentRuntime | Tool devuelve output validable por contrato. |

Termino clave: "contrato" significa una forma de entrada/salida que dos modulos
acuerdan y que podemos verificar con tests.

## 4. Cambio minimo recomendado

Mantener el flujo productivo como autoridad y aislar lo experimental:

- Core/domain logic: `app/schemas/`, `app/domain/`, partes de `app/policies/`.
- Runtime: `app/runtime/`, con `orchestrator.py` como coordinador actual.
- Infraestructura: `app/core/`, `app/api/`, `app/adapters/`,
  `app/services/approval/`.
- Tools: `app/tools/`.
- Laboratorio: `runtime_lab/`.
- Documentacion: `docs/` como fuente primaria; `docs_esp/` como espejo con
  riesgo de drift.

## 5. Explicacion pedagogica

Puedes leer NUCLEO como una cadena de filtros:

1. La API recibe una peticion.
2. El Planner propone una accion, pero no decide si es segura.
3. PolicyEngine decide si esa accion se permite.
4. ToolRegistry confirma que la tool existe en produccion.
5. La tool valida input/output y ejecuta solo si runtime lo permite.

La idea importante es separar "proponer", "autorizar" y "ejecutar". Mezclar
esas tres cosas haria el sistema menos verificable.

## 6. Pasos exactos para hacerlo

Orden recomendado de lectura del core:

1. `app/schemas/requests.py`
2. `app/schemas/execution.py`
3. `app/policies/models.py`
4. `app/policies/engine.py`
5. `app/tools/registry.py`
6. `app/runtime/planner.py`
7. `app/runtime/orchestrator.py`
8. `app/services/approval/approval_store.py`
9. `app/api/routes/agent.py`
10. `app/main.py`

## 7. Como comprobar si ha quedado bien

Validacion de arquitectura minima:

```bash
.venv/bin/python -m pytest -q
```

Validacion manual del endpoint productivo:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Luego llamar:

```bash
curl -sS -X POST http://127.0.0.1:8000/agent/run \
  -H 'Authorization: Bearer dev-jose-key' \
  -H 'Content-Type: application/json' \
  -d '{"input":"system info","dry_run":true}'
```

Resultado esperado: respuesta JSON con `status`, `result`, `errors`,
`trace_id` y `version`.

## 8. Riesgos o dudas pendientes

- CRITICO: `orchestrator.py` es el archivo mas delicado; cualquier extraccion
  debe preservar dry_run, approval gate, policy re-evaluation y tool validation.
- CRITICO: `model_router.py` cruza de `app/` a `runtime_lab/`; conviene
  estabilizar esa frontera antes de moverla.
- INFORMATIVO: `planner_augmentation.py` parece modulo de compatibilidad; no
  debe borrarse mientras tests o evals lo importen.
- PREMATURO: convertir laboratorios en paquete productivo.

