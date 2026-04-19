> Nota de consistencia documental (2026-04-19): docs_esp/ es actualmente un espejo parcial en español. La fuente primaria de verdad documental del repositorio es docs/. Si hay discrepancia con el código o con docs/, prevalece docs/ y la arquitectura verificada en código.

# AuditorÃ­a de archivos

## PropÃ³sito

Registrar quÃ© partes del repositorio han sido auditadas.

Este documento no duplica auditorÃ­as detalladas.  
Solo indica cobertura y referencias.

---

## MÃ³dulos auditados

- `app/services/agent_service.py` â†’ ver `docs/modules/agent_service.md`  
- `app/runtime/orchestrator.py` â†’ ver `docs/modules/orchestrator.md`  
- `app/runtime/planner.py` â†’ ver `docs/modules/planner.md`  
- `app/policies/engine.py` â†’ ver `docs/modules/policy_engine.md`  
- `app/tools/base.py` â†’ ver `docs/modules/base_tool.md`  
- `app/tools/registry.py` â†’ ver `docs/modules/tool_registry.md`  

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

El sistema es modular y estÃ¡ correctamente separado, pero depende en gran medida de contratos implÃ­citos:

- el contrato planner â†’ runtime no estÃ¡ validado  
- la entrada/salida de las tools no estÃ¡ estructurada  
- la policy no aplica modos de ejecuciÃ³n  
- el runtime no gestiona fallos  

La arquitectura es sÃ³lida, pero aÃºn se encuentra en fase bootstrap.