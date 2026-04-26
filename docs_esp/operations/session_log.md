> Archivo origen: `docs/operations/session_log.md`
> Última sincronización: `2026-04-26`

# Session log

## 2026-04-10

- Se implementó la orquestación del runtime.
- Se añadieron las tools `echo` y `system_info`.
- Se introdujo una primera capa de policy.
- Se intentó integrar execution context.
- Se revirtió el primer intento de context por exceso de alcance en el refactor.

## 2026-04-11

- Se auditó:
  - `main.py`
  - `api/routes/agent.py`
  - `runtime/orchestrator.py`
- Se aclaró la estructura del runtime:
  - API -> AgentService -> Runtime -> Planner -> Policy -> Registry -> Tool -> Response
- Se identificaron limitaciones:
  - sin execution tracing
  - dependencias globales en runtime
  - planner simple
  - policy engine básico
  - respuesta no estructurada

## 2026-04-12

- Continuó la auditoría del sistema sobre:
  - planner
  - policy engine
  - tool registry
  - base tool
  - implementaciones de tools
- Se verificó el flujo planner -> policy -> registry -> tool.
- Se reorganizaron las tools hacia `tools/local/`.
- Se añadieron directorios reservados o preparatorios:
  - `clients/`
  - `audit/`
  - `runtime/dispatcher.py`
- Se introdujo `AgentService` como capa de servicio separada.

## 2026-04-13

- Se completó la auditoría técnica de:
  - AgentService
  - AgentRuntime
  - Planner
  - PolicyEngine
  - ToolRegistry
  - BaseTool
- Se identificaron gaps críticos:
  - contratos implícitos
  - no enforcement de dry-run
  - manejo limitado de errores en runtime
  - salida de tools no estructurada
  - policy name-based
- Se reorganizó la documentación en:
  - architecture
  - vision
  - planning
  - operations
  - audits

## 2026-04-13 - Integración de Authentication y ExecutionContext

- Se implementó autenticación por API key con alcance de request.
- Se añadió `ExecutionContext`.
- Se propagó el context a través de:
  - route dependency
  - AgentService
  - AgentRuntime
  - PolicyEngine
  - tools
- Se verificó el comportamiento de policy sensible a rol para `system_info`.

## 2026-04-18 - Preservación de resultado estructurado

- Se modificó:
  - `app/schemas/responses.py`
  - `app/runtime/orchestrator.py`
- Se preservó la salida estructurada de las tools en `AgentResponse.result`.
- Se mantuvo `message=str(result)` por compatibilidad hacia atrás.

## 2026-04-19 - Skeleton experimental para expansión de tools con LLM

- Se añadieron módulos experimentales aislados para:
  - proposals de tools
  - generación de tools
  - staging registry
  - audit store
- Se añadió el flag de request `experimental_tool_generation`.
- Se añadió señalización de capability gap en el planner.
- Se añadió una rama de runtime controlada para:
  - creación de proposals
  - registro en staging
  - generación de skeletons
  - generación de artefactos de audit
- Se mantuvo sin cambios el registry de tools de producción.
- La integración real con LLM sigue sin implementarse.

## 2026-04-19 - Normalización de documentación

- Se auditó la documentación Markdown en todo el repositorio.
- Se definieron capas documentales:
  - arquitectura verificada
  - visión objetivo
  - operación
  - auditorías
  - session logs
- Se normalizaron los documentos primarios bajo `docs/`.
- Se marcó `docs_esp/` como traducción mantenida en lugar de fuente primaria verificada.
- Se añadieron:
  - `docs/audits/documentation_consistency_audit.md`
  - `docs/operations/session_log_docs_normalization.md`

## 2026-04-23

- Se recuperó la línea base del sistema después de rollback.
- Se identificaron issues críticos:
  - `PolicyDecision` no estaba cerrado
  - riesgo de drift entre Policy y Registry
  - falta de runner determinista
- Se entró en fase HARDENING:
  - contratos
  - determinismo

## 2026-04-25

- Se añadió trazabilidad interna mínima del runtime:
  - `ExecutionTrace`
  - `ExecutionStep`
  - `Tracer`
  - `InMemoryTracer`
- Se integró tracing en `AgentRuntime` para:
  - resultado del planner
  - decisión de policy
  - resolución de registry
  - ejecución de tool o salto por dry-run
- Se mantuvo la traza interna fuera del contrato público `AgentResponse`.
- Se reforzó `dry_run=True` como comportamiento sin ejecución real, manteniendo
  el paso previsto de tool como `skipped` en la traza.
- Se añadió cobertura unittest para:
  - ejecución permitida
  - ejecución denegada
  - dry-run
  - tool desconocida
  - error de tool
  - fallo de tracer
  - contrato de respuesta API
- Se endureció el contrato del planner:
  - se añadió `PlannedAction` tipado
  - se redujeron los estados del planner a `planned` y `no_plan`
  - `no_plan` quedó como resultado válido sin ejecución
  - el runtime se detiene antes de policy si el output del planner no es válido
  - el runtime valida `ToolRegistry` antes de autorizar mediante policy

## 2026-04-26 - Runtime Audit UI y CORS local

- Se añadió una Runtime Audit UI estática mínima en:
  - `runtime_lab/runtime_audit_ui/frontend/index.html`
  - `runtime_lab/runtime_audit_ui/README.md`
- Se mantuvo la UI como verificador del contrato HTTP:
  - llama a `POST /agent/run`
  - llama a `GET /tools`
  - llama a `GET /health`
  - muestra el JSON completo del backend
  - no decide tools
  - no evalúa policy
  - no modifica la ejecución del runtime
  - no llama a `runtime_lab/llm_lab`
- Se añadió `GET /health` como alias de la ruta de salud existente.
- Se añadió CORS solo para desarrollo local en `app/main.py` para los origins:
  - `http://127.0.0.1:8766`
  - `http://127.0.0.1:8767`
  - `http://localhost:8766`
  - `http://localhost:8767`
- Métodos CORS permitidos:
  - `GET`
  - `POST`
  - `OPTIONS`
- Headers CORS permitidos:
  - `Authorization`
  - `Content-Type`
- Se preservaron los límites de arquitectura:
  - sin cambios en `AgentService`
  - sin cambios en `AgentRuntime`
  - sin cambios en `Planner`
  - sin cambios en `PolicyEngine`
  - sin cambios en `ToolRegistry`
  - sin cambios en tools
  - sin cambios en `AgentResponse`
- Se documentó la carencia de trazabilidad pública:
  - `AgentResponse` no expone `request_id` top-level
  - cualquier request ID dentro de `result` depende de cada tool y no está
    garantizado por el contrato público
- Se validó:
  - compilación Python de archivos FastAPI modificados
  - descubrimiento unittest
  - peticiones `OPTIONS` equivalentes a preflight de navegador desde
    `http://127.0.0.1:8767`
  - `GET /health`
  - `GET /tools`
  - `POST /agent/run` con `dry_run=true`
