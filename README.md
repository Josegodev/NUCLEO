# NUCLEO

## Visión general

NUCLEO es un runtime de agentes modulares construido sobre FastAPI.

Ejecuta peticiones de usuario a través de un pipeline controlado:

- **Planner** → decide qué herramienta utilizar  
- **Policy Engine** → valida la ejecución  
- **Tool Registry** → resuelve la herramienta  
- **Tool** → ejecuta la acción  

**Objetivo:**  
Proporcionar un sistema de ejecución **controlado y auditable**, evitando comportamientos tipo “caja negra”.

---

## Arquitectura (alto nivel)

Request  
→ API  
→ AgentService  
→ Runtime  
→ Planner  
→ Policy  
→ ToolRegistry  
→ Tool  
→ Response  

Para más detalle:

- `docs/architecture.md`  
- `docs/evolution_map.md`  

---

## Contexto de ejecución

El sistema expone una API HTTP utilizando FastAPI y es ejecutado mediante Uvicorn.

- **FastAPI** define los endpoints, valida las peticiones y estructura las respuestas.  
- **Uvicorn** actúa como servidor ASGI que ejecuta la aplicación y gestiona las conexiones HTTP.  

---

## Estado del proyecto

⚠️ Fase actual: bootstrap

Actualmente:

- Arquitectura modular definida
- Pipeline de ejecución funcional end-to-end
- Auditoría técnica completada

Pendiente:

- Refuerzo de contratos (ExecutionPlan, schemas)
- Control de ejecución (`dry_run`)
- Manejo de errores
- Persistencia (base de datos)
- Evolución de planner y policy

---

## Ejemplo de uso

### Request

```json
{
  "user_input": "system info",
  "dry_run": true
}

### Flujo de ejecución

Cliente HTTP  
↓  
Uvicorn  
↓  
FastAPI (/run endpoint)  
↓  
AgentService  
↓  
AgentRuntime  
↓  
Planner → Policy → Tool  
↓  
Respuesta  

### Arranque del sistema

```md
```bash
uvicorn app.main:app --reload


## Documentación

- Inglés: `docs/`
- Español: `docs_esp/`