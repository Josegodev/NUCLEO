# NUCLEO

NUCLEO es un runtime de agentes modulares construido sobre FastAPI.

Ejecuta peticiones de usuario a través de un pipeline controlado:

- Planner → decide qué herramienta utilizar  
- Policy Engine → valida la ejecución  
- Tool Registry → resuelve la herramienta  
- Tool → ejecuta la acción  

**Objetivo:**  
Proporcionar un sistema de ejecución controlado y auditable, evitando comportamientos tipo “caja negra”.

---

## Quick start (2 minutos)

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar el servidor

```bash
uvicorn app.main:app --reload
```

### 3. Abrir Swagger

```
http://127.0.0.1:8000/docs
```

---

## Autenticación

El sistema utiliza API Key por request.

En Swagger:

1. Pulsa **Authorize**  
2. Introduce:

```
dev-jose-key
```

---

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
  -d '{"user_input": "system info", "dry_run": false}'
```

### Response (actual)

```json
{
  "status": "success",
  "message": "{'requested_by': 'jose', 'request_id': '...', 'os': 'Windows', ...}"
}
```

---

## Arquitectura

```
Request
→ API
→ AgentService
→ Runtime
→ Planner
→ Policy
→ ToolRegistry
→ Tool
→ Response
```

### Más detalle

- `docs/architecture.md`
- `docs/evolution_map.md`

---

## Flujo de ejecución

```
Cliente HTTP
↓
Uvicorn
↓
FastAPI (/agent/run)
↓
AgentService
↓
AgentRuntime
↓
Planner → Policy → Tool
↓
Respuesta
```

---

## Estado del proyecto

### ⚠️ Fase actual: bootstrap

### Implementado

- Arquitectura modular  
- Pipeline de ejecución funcional end-to-end  
- Autenticación por API key  
- ExecutionContext propagado  
- Policy básica basada en roles  

### Pendiente

- Response estructurado (actualmente serializado como string)  
- Logging / auditoría  
- Persistencia (base de datos)  
- Mejora del planner  
- Validación de payload  

---

## Contexto técnico

El sistema expone una API HTTP utilizando FastAPI y es ejecutado mediante Uvicorn.

- FastAPI define endpoints, validación y estructura de respuesta  
- Uvicorn ejecuta la aplicación como servidor ASGI  