# NUCLEO

NUCLEO es un runtime de agentes modulares construido sobre FastAPI. Su objetivo es ejecutar peticiones de usuario mediante un pipeline controlado y auditable, evitando comportamientos opacos y separando con claridad decisión, validación y ejecución.

## Qué hace (en 30 segundos)

NUCLEO permite automatizar tareas sobre datos reales de forma controlada.

Ejemplo real:

- Input: datos de producción con errores (CSV incompletos, valores ambiguos)
- Proceso: validación estructural + decisión controlada
- Output: datos limpios y agregados listos para uso operativo

### Ejemplo

Input:caja_1,caja_2,caja_3
5,,8
,, 
10,6,x

Output:
Trabajador A → 13 kg
Errores detectados → 2 filas inválidas

Esto evita ejecutar acciones sobre datos incorrectos y permite automatizar procesos manteniendo control total sobre la ejecución.

## Uso de IA (controlado)

NUCLEO está diseñado para integrar modelos de lenguaje (LLMs) sin perder control del sistema.

Uso actual:

- interpretación de valores ambiguos
- limpieza de datos no estructurados
- asistencia en validación
- augmentación controlada del Planner para producir propuestas estructuradas

El modelo nunca ejecuta directamente acciones:
todas pasan por validación explícita en el runtime.

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
→ Tool / Proposal
→ AgentResponse

### Componentes verificados

- `Planner` adapta intención a una acción candidata determinista.
- `Planner` puede usar augmentación LLM controlada en `proposal_only`, pero solo
  para producir una propuesta validada.
- `ToolRegistry` es la fuente de verdad de tools ejecutables.
- `PolicyEngine` autoriza la ejecución según autenticación, rol y nombre de tool.
- `Tool` ejecuta la acción real.
- `AgentResponse` devuelve `status`, `result`, `errors`, `trace_id` y `version`.

### Agent Runtime (Controlled Execution)

El flujo controlado actual es:

```text
Request
-> Planner (determinista + LLM augmentation)
-> PolicyEngine
-> ToolRegistry
-> Proposal (dry_run)
-> Approval Gate
-> Execution
```

Hay tres conceptos separados:

- `proposal_only`: el Planner puede usar el LLM para proponer una acción, pero
  la salida se normaliza, se parsea como JSON y se valida contra contratos reales
  de `ToolRegistry`.
- `approve`: `POST /agent/approve` recibe solo `trace_id` y `approved`; no llama
  al Planner ni al LLM.
- execution: una tool solo se ejecuta después de recuperar la proposal
  persistida, revalidar `PolicyEngine`, resolver de nuevo `ToolRegistry` y
  validar el payload contra el contrato de la tool.

Garantías actuales:

- el LLM no ejecuta tools
- `PolicyEngine` interviene antes de cualquier ejecución real
- la validación de payload es estricta y no acepta campos extra
- si la salida LLM es inválida, se usa fallback determinista
- `dry_run=true` no llama a `tool.run(...)`
- una proposal ya `EXECUTED` no se reejecuta en una segunda aprobación

## Estado actual del runtime

### Implementado actualmente

- API FastAPI funcional
- Endpoint `POST /agent/run`
- Endpoint `POST /agent/approve`
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
  - `proposal_only` persiste proposals por `trace_id`
  - `/agent/approve` ejecuta solo proposals persistidas y aprobadas
  - trazabilidad interna mínima en memoria para el runtime

### Experimental, no producción

Existen módulos y artefactos de laboratorio aislados en `runtime_lab/`, pero no
son autoridad de ejecución. La única reutilización productiva actual es
`runtime_lab/llm_lab/model_adapter.py` a través de
`app/adapters/model_router.py`, exclusivamente como frontera de modelo para la
augmentación controlada del Planner.

### LLM Lab / Ruta lateral experimental

`runtime_lab/llm_lab/` vive dentro del repositorio para facilitar observación y
consultas locales con modelos. Sus experimentos siguen fuera del runtime de
NUCLEO. El runtime productivo no llama directamente a esta capa; usa
`app/adapters/model_router.py`.

Propósito:

- cargar contexto documentado de NUCLEO para revisión externa
- ejecutar chats locales de laboratorio con SQLite y Ollama
- generar informes markdown de revisión HARDENING

Estado actual:

- experimental
- ruta lateral de solo observación respecto al runtime productivo
- sin autoridad sobre `AgentService`, `AgentRuntime`, `Planner`,
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
- ejecución remota opcional en experimentos mediante `model_id` prefijado
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

El mismo modo `ollama` se conserva como ruta de ejecución real por
compatibilidad. `model_adapter.py` infiere el proveedor desde el `model_id`:

```text
qwen                 -> Ollama local
mistral              -> Ollama local
llama3.1:8b          -> Ollama local
openai:gpt-4o        -> OpenAI-compatible
a-... -> Anthropic
google:gemini-...    -> Google
```

Las claves remotas se leen solo desde variables de entorno:

```text
OPENAI_API_KEY
OPENAI_BASE_URL   # opcional
ANTHROPIC_API_KEY
GOOGLE_API_KEY
```

Estas claves no se guardan en artefactos. El schema de artefacto sigue siendo
`llm_lab.experiment.v1`.

### llm_lab UI / Productive Agent Console v0

`runtime_lab/llm_lab_ui/` contiene actualmente la consola local
`Productive Agent Console v0`.

La consola:

- llama al endpoint real `POST /agent/run`
- envía `agent_mode="proposal_only"` y `dry_run=true`
- permite seleccionar `backend` y `model_id`
- muestra proposal, modelo usado, backend usado y latencia
- puede llamar a `POST /agent/approve` para aprobar o rechazar una proposal
- no ejecuta tools
- no decide política
- no permite que un LLM ejecute tools ni controle el runtime

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

Referencia: `docs_esp/productive_agent_console_v0.md`.

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

- Promoción automática desde staging a producción
- Ejecución de tools generadas en el registry principal
- Exposición pública de trazas por API
- Persistencia de trazas fuera de memoria
- Memoria conversacional
- Tool chaining o ejecución multi-step

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
  "input": "haz echo de hola",
  "context": {},
  "options": {
    "backend": "openai",
    "model_id": "gpt-4o-mini",
    "agent_mode": "proposal_only",
    "dry_run": true
  }
}
```

### curl

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Authorization: Bearer dev-jose-key" \
  -H "Content-Type: application/json" \
  -d "{\"input\":\"haz echo de hola\",\"context\":{},\"options\":{\"backend\":\"openai\",\"model_id\":\"gpt-4o-mini\",\"agent_mode\":\"proposal_only\",\"dry_run\":true}}"
```

### Response actual

```json
{
  "status": "success",
  "result": {
    "dry_run": true,
    "executed": false,
    "execution_allowed": false,
    "tool": "echo",
    "payload": {
      "text": "hola"
    },
    "execution_state": "PROPOSED"
  },
  "trace_id": "trace-..."
}
```

En `dry_run=true`, el runtime ejecuta Planner, PolicyEngine y ToolRegistry,
pero no llama a `Tool.run(...)`. La respuesta indica la tool que se habría
ejecutado y marca `executed=false`.

## Flujo de ejecución

Cliente HTTP
↓
FastAPI (`/agent/run`)
↓
AgentService
↓
AgentRuntime
↓
Planner → PolicyEngine → ToolRegistry → dry_run proposal
↓
Approval Gate (`/agent/approve`)
↓
PolicyEngine → ToolRegistry → Tool
↓
AgentResponse / ApprovalResponse

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
