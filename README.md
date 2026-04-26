# NUCLEO

NUCLEO es un runtime de agentes modulares construido sobre FastAPI. Su objetivo es ejecutar peticiones de usuario mediante un pipeline controlado y auditable, evitando comportamientos opacos y separando con claridad decisión, validación y ejecución.

## Estado documental

La documentación del repositorio sigue esta convención:

- `docs/architecture.md` describe arquitectura verificada en código.
- `docs/vision/architecture_vision.md` describe arquitectura objetivo.
- `docs/operations/` recoge estado operativo y session logs.
- `docs/audits/` recoge evaluaciones críticas y consistencia documental.

Si un documento describe una capacidad futura o experimental, debe indicarlo explícitamente.

## Arquitectura verificada

El flujo estable actual es:

Request  
→ API  
→ AgentService  
→ AgentRuntime  
→ Planner  
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse

### Componentes verificados

- `Planner` adapta intención a una acción candidata determinista.
- `ToolRegistry` es la fuente de verdad de tools ejecutables.
- `PolicyEngine` autoriza la ejecución según autenticación, rol y nombre de tool.
- `Tool` ejecuta la acción real.
- `AgentResponse` devuelve `status`, `message` y `result` opcional.

## Estado actual del runtime

### Implementado actualmente

- API FastAPI funcional
- Endpoint `POST /agent/run`
- Endpoint `GET /tools`
- Endpoint `GET /`
- Endpoint `GET /health`
- Autenticación por API key por request
- `ExecutionContext` propagado por runtime, policy y tools
- Tools de producción:
  - `echo`
  - `system_info`
  - `disk_info`
- Resultado estructurado conservado en `AgentResponse.result`
- Fase HARDENING en curso:
  - contratos runtime-policy-registry más explícitos
  - Planner devuelve `planned` o `no_plan`
  - `no_plan` no ejecuta tools
  - `dry_run` no ejecuta la tool real
  - trazabilidad interna mínima en memoria para el runtime

### Experimental, no producción

Existen módulos y artefactos de laboratorio aislados en `runtime_lab/`, pero no
forman parte del contrato estable actual del Planner. El Planner estable solo
devuelve `planned` o `no_plan`.

### LLM Lab / Ruta lateral experimental

`runtime_lab/llm_lab/` vive dentro del repositorio para facilitar observación y
consultas locales con Mistral/Qwen, pero no está integrado en el runtime de
NUCLEO.

Propósito:

- cargar contexto documentado de NUCLEO para revisión externa
- ejecutar chats locales de laboratorio con SQLite y Ollama
- generar informes markdown de revisión HARDENING

Estado actual:

- experimental
- ruta lateral de solo observación respecto al runtime productivo
- sin integración con `AgentService`, `AgentRuntime`, `Planner`,
  `PolicyEngine`, `ToolRegistry` ni `Tools`

Prohibido para esta ruta:

- ejecutar tools de producción
- modificar policy
- llamar automáticamente a `/agent/run`
- actuar como Planner
- registrar tools en el `ToolRegistry` de producción

Referencia operativa: `docs/operations/operational_state.md`.

## llm_lab (Experimental Layer)

`runtime_lab/llm_lab/` es una capa experimental para ejecutar comparaciones
deterministas entre modelos locales y guardar artefactos auditables.

Propósito:

- experimentación multi-modelo fuera del runtime principal
- ejecución local con modelos disponibles vía Ollama
- conservación de resultados como artefactos JSON versionados
- validación explícita de errores, rankings y síntesis

No forma parte de NUCLEO core. No llama a `AgentService`, `AgentRuntime`,
`Planner`, `PolicyEngine`, `ToolRegistry`, `Tools` ni `AgentResponse`.

Componentes principales:

- `runtime_lab/llm_lab/experiment_runner.py`
- `runtime_lab/llm_lab/experiment_artifact.py`
- `runtime_lab/llm_lab/experiment_validator.py`
- `runtime_lab/docs/llm_lab_experiment_artifact_contract.md`

Los experimentos producen:

```text
runtime_lab/llm_lab/artifacts/{experiment_id}.json
```

Los artefactos generados no se versionan salvo `.gitkeep`.

### Running experiments

Mock determinista con errores explícitos:

```bash
python runtime_lab/llm_lab/experiment_runner.py \
  --mode mock \
  --input "Compara inferencia local y remota en fase HARDENING"
```

Mock determinista exitoso:

```bash
python runtime_lab/llm_lab/experiment_runner.py \
  --mode mock-success \
  --input "Resume el objetivo de un artefacto auditable"
```

Ollama local, si `qwen` y `mistral` están disponibles:

```bash
python runtime_lab/llm_lab/experiment_runner.py \
  --mode ollama \
  --stage1-models qwen,mistral \
  --stage2-reviewers qwen,mistral \
  --chairman qwen \
  --input "Explica el contrato de artefactos de llm_lab"
```

### llm_lab UI

`runtime_lab/llm_lab_ui/` contiene una UI local opcional para lanzar
experimentos y visualizar artefactos.

La UI:

- interactúa solo con `runtime_lab/llm_lab`
- lee artefactos desde `runtime_lab/llm_lab/artifacts/`
- no llama al runtime de NUCLEO
- no ejecuta tools
- no decide política
- no integra proveedores externos

Arranque local:

```bash
python -m uvicorn runtime_lab.llm_lab_ui.backend.main:app \
  --host 127.0.0.1 \
  --port 8765
```

Abrir:

```text
http://127.0.0.1:8765/
```

Referencia: `runtime_lab/docs/llm_lab_ui_interaction.md`.

### Runtime Audit UI (Local Dev)

`runtime_lab/runtime_audit_ui/` contiene una consola estática mínima para
verificar el contrato HTTP del runtime de NUCLEO desde navegador.

La UI:

- llama a `POST /agent/run`
- llama a `GET /tools`
- llama a `GET /health`
- muestra la respuesta completa como JSON
- no decide tools
- no evalúa policy
- no modifica el runtime
- no integra LLMs
- no llama a `runtime_lab/llm_lab`

Arranque local recomendado:

```bash
.venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8001
```

```bash
.venv/bin/python -m http.server 8767 \
  --directory runtime_lab/runtime_audit_ui/frontend
```

Abrir:

```text
http://127.0.0.1:8767/
```

En la UI, configurar `API base URL` como:

```text
http://127.0.0.1:8001
```

El CORS local para esta consola está declarado en `app/main.py` y permite solo:

- `http://127.0.0.1:8766`
- `http://127.0.0.1:8767`
- `http://localhost:8766`
- `http://localhost:8767`

Métodos permitidos: `GET`, `POST`, `OPTIONS`.

Headers permitidos: `Authorization`, `Content-Type`.

Nota de trazabilidad: `AgentResponse` no expone actualmente un `request_id`
top-level. Algunas tools pueden incluirlo dentro de `result`, pero no es parte
garantizada del contrato público.

### External audits

`external/` se usa solo como área de investigación y auditoría externa.

Referencias auditadas:

- `external/shimmy`: candidato externo de backend de inferencia.
- `external/llm-council`: referencia conceptual para orquestación de
  experimentos multi-modelo en `llm_lab`.

Estas referencias no forman parte del runtime de NUCLEO y no deben ser usadas
como dependencias del core. Los informes se guardan bajo `runtime_lab/audit/`.

### No implementado todavía

- Integración real con LLM para planificación
- Integración de Mistral/Qwen en el flujo canónico
- Promoción automática desde staging a producción
- Ejecución de tools generadas en el registry principal
- Persistencia operativa del runtime más allá de artefactos de laboratorio
- Exposición pública de trazas por API
- Persistencia de trazas fuera de memoria

## Quick start:

source .venv/bin/activate

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar el servidor

```bash
uvicorn app.main:app --reload
```

### 3. Abrir Swagger

```text
http://127.0.0.1:8000/docs
```

## Autenticación

El sistema utiliza API key por request mediante `Authorization: Bearer <token>`.

Clave de desarrollo disponible en la configuración actual:

- `dev-jose-key`

## Ejemplo de uso

### Request

```json
{
  "user_input": "system info",
  "dry_run": true
}
```

### curl

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Authorization: Bearer dev-jose-key" \
  -H "Content-Type: application/json" \
  -d "{\"user_input\": \"system info\", \"dry_run\": true}"
```

### Response actual

```json
{
  "status": "dry_run_success",
  "message": "{'dry_run': True, 'executed': False, 'tool': 'system_info', 'payload': {}}",
  "result": {
    "dry_run": true,
    "executed": false,
    "tool": "system_info",
    "payload": {}
  }
}
```

En `dry_run=true`, el runtime ejecuta Planner, PolicyEngine y ToolRegistry,
pero no llama a `Tool.run(...)`. La respuesta indica la tool que se habría
ejecutado y marca `executed=false`.

## Flujo de ejecución

Cliente HTTP  
↓  
Uvicorn  
↓  
FastAPI (`/agent/run`)  
↓  
AgentService  
↓  
AgentRuntime  
↓  
Planner → PolicyEngine → ToolRegistry → Tool / dry_run  
↓  
AgentResponse

Si el Planner devuelve `no_plan`, el Runtime no consulta PolicyEngine y no
ejecuta ninguna tool. El Planner no autoriza y no ejecuta; solo propone.

La trazabilidad de ejecución existe como mecanismo interno en memoria del
runtime. No forma parte del contrato público de `/agent/run`, no se persiste y
no se expone todavía mediante endpoint.

## Referencias útiles

- `docs/architecture.md`
- `docs/vision/architecture_vision.md`
- `docs/EVOLUTION_MAP.md`
- `docs/audits/documentation_consistency_audit.md`
