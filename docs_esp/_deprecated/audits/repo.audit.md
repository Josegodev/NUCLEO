> Nota de consistencia documental (2026-04-19): docs_esp/ es actualmente un espejo parcial en español. La fuente primaria de verdad documental del repositorio es docs/. Si hay discrepancia con el código o con docs/, prevalece docs/ y la arquitectura verificada en código.

# AuditorÃ­a del repositorio

## PropÃ³sito

Este documento evalÃºa el repositorio como estructura de cÃ³digo:
- organizaciÃ³n de directorios  
- lÃ­mites entre mÃ³dulos  
- consistencia de nombres  
- riesgos de escalabilidad en la estructura del proyecto  
- alineaciÃ³n entre la estructura fÃ­sica y la arquitectura prevista  

EstÃ¡ basado en la implementaciÃ³n actual auditada.

---

## Estructura actual del repositorio

Estructura de alto nivel (auditada):

## Estructura del repositorio (real)

```text
app/
  -main.py                    â†’ Punto de entrada FastAPI; inicializa la app y registra rutas

  api/
    routes/
      agent.py              â†’ POST `/agent/run`; ejecuta el agente vÃ­a AgentService
      health.py             â†’ GET `/health`; endpoint de estado (liveness)
      tools.py              â†’ GET `/tools`; expone tools registradas

  -services/
    agent_service.py        â†’ Fachada ligera; delega la ejecuciÃ³n en AgentRuntime

  -runtime/
    orchestrator.py         â†’ Pipeline de ejecuciÃ³n central; coordina planner, policy y tools
    planner.py              â†’ LÃ³gica de decisiÃ³n basada en reglas; mapea user_input â†’ tool + payload
    dispatcher.py           â†’ (planificado) router de ejecuciÃ³n; decidirÃ¡ dÃ³nde/cÃ³mo se ejecutan las tools

  -policies/
    engine.py               â†’ Control de ejecuciÃ³n; permite/deniega en base al nombre de la tool
    models.py               â†’ Esquema PolicyDecision (decision + reason)

  -tools/
    base.py                 â†’ DefiniciÃ³n de interfaz de tool (BaseTool)
    registry.py             â†’ Registro de tools; resuelve tools por nombre
    local/                  â†’ Implementaciones concretas (ej. echo, system_info)

  -schemas/
    requests.py             â†’ Modelo AgentRequest (contrato de entrada)
    responses.py            â†’ Modelo AgentResponse (contrato de salida)
    execution.py            â†’ Modelos de ejecuciÃ³n (PlanStep, ToolResult)

docs/
  -architecture.md           â†’ Comportamiento verificado del sistema (fuente de verdad)
  -evolution_map.md          â†’ Roadmap tÃ©cnico y prioridades de evoluciÃ³n

  -modules/                  â†’ AuditorÃ­a por mÃ³dulo (runtime, planner, etc.)
  -audits/                   â†’ AuditorÃ­as de repositorio y archivos
  -operations/               â†’ Estado operativo, session log, snapshots
  -planning/                 â†’ Plan de desarrollo y siguientes pasos
  -vision/                   â†’ Arquitectura objetivo (diseÃ±o futuro)