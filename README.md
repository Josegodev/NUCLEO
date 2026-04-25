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

- `Planner` decide qué herramienta utilizar.
- `PolicyEngine` valida la ejecución según autenticación, rol y nombre de tool.
- `ToolRegistry` resuelve la herramienta por nombre.
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
- Resultado estructurado conservado en `AgentResponse.result`

### Experimental, no producción

Existe una ruta experimental de laboratorio para propuestas y skeletons de tools asistidas por LLM. Está aislada en `runtime_lab/`, no auto-registra tools en producción y solo se activa mediante la señalización experimental del request.

### No implementado todavía

- Integración real con LLM para planificación
- Promoción automática desde staging a producción
- Ejecución de tools generadas en el registry principal
- Persistencia operativa del runtime más allá de artefactos de laboratorio
- Trazabilidad completa de producción integrada en el pipeline estable

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

```text
dev-jose-key
```

## Ejemplo de uso

### Request

```json
{
  "user_input": "system info",
  "dry_run": false
}
```

### curl

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Authorization: Bearer dev-jose-key" \
  -H "Content-Type: application/json" \
  -d "{\"user_input\": \"system info\", \"dry_run\": false}"
```

### Response actual

```json
{
  "status": "success",
  "message": "{'requested_by': 'jose', 'request_id': '...', 'os': 'Windows', ...}",
  "result": {
    "requested_by": "jose",
    "request_id": "...",
    "os": "Windows"
  }
}
```

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
Planner → Policy → ToolRegistry → Tool  
↓  
AgentResponse

## Referencias útiles

- `docs/architecture.md`
- `docs/vision/architecture_vision.md`
- `docs/EVOLUTION_MAP.md`
- `docs/audits/documentation_consistency_audit.md`
