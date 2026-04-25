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
