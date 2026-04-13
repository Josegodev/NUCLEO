# Auditoría de archivos

## Propósito

Registrar qué partes del repositorio han sido auditadas.

Este documento no duplica auditorías detalladas.  
Solo indica cobertura y referencias.

---

## Módulos auditados

- `app/services/agent_service.py` → ver `docs/modules/agent_service.md`  
- `app/runtime/orchestrator.py` → ver `docs/modules/orchestrator.md`  
- `app/runtime/planner.py` → ver `docs/modules/planner.md`  
- `app/policies/engine.py` → ver `docs/modules/policy_engine.md`  
- `app/tools/base.py` → ver `docs/modules/base_tool.md`  
- `app/tools/registry.py` → ver `docs/modules/tool_registry.md`  

---

## Revisados estructuralmente

- `app/main.py`  
- `app/api/routes/*`  
- `app/policies/models.py`  
- `app/schemas/*`  
- `app/runtime/dispatcher.py`  

(cubiertos en `repo_audit.md`)

---

## Resumen

El sistema es modular y está correctamente separado, pero depende en gran medida de contratos implícitos:

- el contrato planner → runtime no está validado  
- la entrada/salida de las tools no está estructurada  
- la policy no aplica modos de ejecución  
- el runtime no gestiona fallos  

La arquitectura es sólida, pero aún se encuentra en fase bootstrap.