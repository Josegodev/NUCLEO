# Snapshot del sistema – NUCLEO

## Propósito

Este documento captura el estado operativo actual del sistema
en el momento de la migración a un nuevo entorno Linux.

Refleja el estado real de la implementación y los cambios estructurales recientes.

---

## Visión general del sistema

El sistema es un runtime de agentes modulares construido con FastAPI.

Pipeline de ejecución (implementación actual):

AgentRequest  
→ AgentService  
→ AgentRuntime  
→ Planner  
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse  

---

## Arquitectura actual

- `api/` → rutas HTTP (FastAPI)  
- `runtime/` → orquestación de ejecución  
- `policies/` → control de ejecución  
- `tools/` → tools ejecutables  
- `schemas/` → modelos de datos  

---

## Refactor reciente

### Reestructuración de tools

- `tools/local/` → ejecución local  
- `tools/remote/` → reservado (no implementado aún)  
- eliminado `tools/implementations/`  

### Nuevas capas introducidas

- `clients/` → capa de comunicación externa planificada (no activa)  
- `audit/` → logging y trazabilidad planificados (no activo)  
- `runtime/dispatcher.py` → presente pero no integrado en el flujo de ejecución  

---

## Tools (actuales)

### echo_tool
- read_only: true  
- comportamiento simple de eco  

### system_info_tool
- read_only: true  
- devuelve metadatos del sistema  

Ambas:
- registradas en ToolRegistry  
- invocables vía `/agent/run`  

---

## Endpoints

### GET /tools
Devuelve la lista de tools registradas  

### POST /agent/run
Ejecuta el runtime del agente  

Ejemplo:

```json
{
  "user_input": "system info",
  "dry_run": true
}