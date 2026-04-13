# Auditoría del repositorio

## Propósito

Este documento evalúa el repositorio como estructura de código:
- organización de directorios  
- límites entre módulos  
- consistencia de nombres  
- riesgos de escalabilidad en la estructura del proyecto  
- alineación entre la estructura física y la arquitectura prevista  

Está basado en la implementación actual auditada.

---

## Estructura actual del repositorio

Estructura de alto nivel (auditada):

## Estructura del repositorio (real)

```text
app/
  -main.py                    → Punto de entrada FastAPI; inicializa la app y registra rutas

  api/
    routes/
      agent.py              → POST `/agent/run`; ejecuta el agente vía AgentService
      health.py             → GET `/health`; endpoint de estado (liveness)
      tools.py              → GET `/tools`; expone tools registradas

  -services/
    agent_service.py        → Fachada ligera; delega la ejecución en AgentRuntime

  -runtime/
    orchestrator.py         → Pipeline de ejecución central; coordina planner, policy y tools
    planner.py              → Lógica de decisión basada en reglas; mapea user_input → tool + payload
    dispatcher.py           → (planificado) router de ejecución; decidirá dónde/cómo se ejecutan las tools

  -policies/
    engine.py               → Control de ejecución; permite/deniega en base al nombre de la tool
    models.py               → Esquema PolicyDecision (decision + reason)

  -tools/
    base.py                 → Definición de interfaz de tool (BaseTool)
    registry.py             → Registro de tools; resuelve tools por nombre
    local/                  → Implementaciones concretas (ej. echo, system_info)

  -schemas/
    requests.py             → Modelo AgentRequest (contrato de entrada)
    responses.py            → Modelo AgentResponse (contrato de salida)
    execution.py            → Modelos de ejecución (PlanStep, ToolResult)

docs/
  -architecture.md           → Comportamiento verificado del sistema (fuente de verdad)
  -evolution_map.md          → Roadmap técnico y prioridades de evolución

  -modules/                  → Auditoría por módulo (runtime, planner, etc.)
  -audits/                   → Auditorías de repositorio y archivos
  -operations/               → Estado operativo, session log, snapshots
  -planning/                 → Plan de desarrollo y siguientes pasos
  -vision/                   → Arquitectura objetivo (diseño futuro)