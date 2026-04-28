> Archivo origen: `docs/architecture.md`
> Última sincronización: `2026-04-28`

# Arquitectura - Estado actual verificado

## Propósito

Este documento es la fuente de verdad para la arquitectura que puede verificarse directamente en el código actual. Describe comportamiento implementado, comportamiento experimental explícito y limitaciones conocidas cuando son observables en el repositorio.

## Convención documental

Este repositorio separa la documentación en capas:

- Arquitectura verificada: comportamiento implementado y verificable en código
- Arquitectura objetivo / visión: diseño futuro previsto
- Operación: estado de ejecución, reglas operativas y logs históricos
- Auditorías: evaluación crítica, riesgos, gaps y comprobaciones de consistencia
- Session logs: registro cronológico de decisiones y cambios

Si una capacidad es experimental, parcial o futura, debe etiquetarse de forma explícita.

## Flujo de ejecución verificado

Flujo estable del runtime:

AgentRequest  
-> AgentService  
-> AgentRuntime  
-> Planner  
-> PolicyEngine  
-> ToolRegistry  
-> Tool  
-> AgentResponse

## Endpoints verificados

- `GET /` -> respuesta de health
- `GET /tools` -> lista de tools de producción registradas
- `POST /agent/run` -> ejecuta el runtime del agente

## Responsabilidades verificadas de los componentes

### API

- Recibe peticiones HTTP
- Resuelve la autenticación en el borde de la request
- Construye `ExecutionContext`
- Delega en `AgentService`

### AgentService

- Fachada ligera de servicio sobre `AgentRuntime`
- Propaga `AgentRequest` y `ExecutionContext`
- No asume planificación, policy ni ejecución de tools

### AgentRuntime

- Coordina el pipeline del runtime
- Invoca al planner
- Invoca al policy engine
- Resuelve tools a través del registry de producción
- Ejecuta tools de producción
- Registra pasos internos de planner, policy, registry y tool mediante el tracer del runtime
- Devuelve un artefacto estructurado `AgentResponse`

### Planner

- Realiza planificación simple basada en reglas
- Actúa como adaptador determinista de intención a acción candidata
- Devuelve un `PlannedAction` tipado y versionado
- No autoriza ni ejecuta tools
- Puede emitir:
  - `planned`
  - `no_plan`

### PolicyEngine

- Requiere un `ExecutionContext` autenticado
- Permite `echo`
- Permite `disk_info`
- Permite `system_info` solo para `admin`
- Deniega cualquier otra tool de producción por nombre
- Devuelve artefactos `PolicyDecision` estrictos usando `PolicyDecisionValue`

### ToolRegistry

- Almacena instancias de tools de producción indexadas por `tool.name`
- Exige que cada tool registrada exponga `ToolContractArtifact`
- Rechaza nombres duplicados y nombres fuera del conjunto cerrado de producción
- Resuelve tools por `tool.name`
- Está separado de staging y de los registries experimentales

### LLM Lab / Ruta lateral experimental

`runtime_lab/llm_lab/` existe dentro del repositorio, pero no forma parte del
flujo estable de ejecución.

Puede:

- cargar contexto documentado del repositorio para revisión externa
- ejecutar chats locales de Mistral/Qwen mediante Ollama
- persistir memoria local de chat en SQLite bajo `runtime_lab/llm_lab/`
- generar informes markdown de revisión HARDENING bajo
  `runtime_lab/llm_lab/reports/`

No debe:

- llamar automáticamente a `AgentService` ni a `/agent/run`
- actuar como Planner
- ejecutar tools de producción
- modificar `PolicyEngine`
- registrar tools en el `ToolRegistry` de producción

### Tools de producción

Actualmente registradas en tiempo de importación en el runtime de producción:

- `echo`
- `system_info`
- `disk_info`

### AgentResponse

El modelo de respuesta actual del runtime contiene:

- `status`
- `result` estructurado opcional
- `errors`
- `trace_id`
- `version`

Breaking change: `message` ya no forma parte del contrato público de respuesta.
El contrato público del resultado de ejecución es `status`, `result`, `errors`,
`trace_id` y `version`.

`status` público está cerrado a:

- `success`
- `error`
- `rejected`

## Contratos actuales verificados

### AgentRequest

Campos actuales:

- `user_input: str`
- `tool: str | None`
- `payload: dict | None`
- `dry_run: bool = True`
- `experimental_tool_generation: bool = False`

La request puede seguir transportando un payload como diccionario, pero el
payload de la acción planificada se valida contra el contrato de la tool
seleccionada antes de ejecutar.

### Salida del Planner

El planner devuelve `PlannedAction`.

Campos actuales:

- `status`
- `tool_name`
- `payload`
- `preconditions`
- `expected_output`
- `confidence`
- `reason`
- `source`
- `version`

`status` puede ser:

- `planned`
- `no_plan`

`no_plan` es un resultado válido. Significa que ninguna regla determinista ha encajado, por lo que el runtime no debe ejecutar ninguna tool.

### PolicyDecision

Campos actuales:

- `decision` (`PolicyDecisionValue.ALLOW` o `PolicyDecisionValue.DENY`)
- `reason`
- `validated_fields`
- `version`

`PolicyDecision` es estricto: usa `strict=True` y `extra="forbid"`.
Decisiones string como `"allow"` o `"deny"` no se aceptan como entrada válida
del contrato.

### Traza del runtime

La trazabilidad interna está implementada en `app/runtime/tracing.py`.

`ExecutionTrace` contiene:

- `trace_id`
- `request_id`
- `steps`

Cada `ExecutionStep` contiene:

- `step_id`
- `phase` (`planner`, `policy`, `registry` o `tool`)
- `input`
- `output`
- `status` (`success`, `denied`, `error` o `skipped`)
- `error`
- `timestamp`

La implementación actual es `InMemoryTracer`. No tiene persistencia en disco ni
integración externa.

## Subsistema experimental verificado

Los módulos experimentales de proposal y staging siguen existiendo en código aislado y en `runtime_lab/`, pero no forman parte del contrato estable actual del Planner.

El Planner actual solo devuelve:

- `planned`
- `no_plan`

El campo `experimental_tool_generation` existe en `AgentRequest`, pero el
runtime estable actual no lo usa para derivar a una ruta de capability gap.

### Regla arquitectónica importante

Las tools experimentales generadas no se auto-registran en el `ToolRegistry` de producción.

## Restricciones y limitaciones verificadas

- La salida del planner está tipada como `PlannedAction` y validada por el runtime
- `PlannedAction` está versionado e incluye precondiciones y salida esperada
- `PolicyDecision` es estricto y basado en enum
- `ToolContractArtifact` es obligatorio para registrar tools de producción
- La validación de payload y output de tools es explícita para las tools registradas
- El runtime devuelve artefactos estructurados de resultado de ejecución con
  estados públicos cerrados
- `dry_run` está impuesto de forma estructural por el runtime: se evalúa policy, se registra el paso de tool y no se ejecuta la tool de producción
- La policy sigue siendo en gran parte name-based
- Metadatos de tools como `read_only` y `risk_level` aún no se aplican desde policy
- El bootstrap de producción sigue ocurriendo en tiempo de importación en `orchestrator.py`

## Explícitamente no verificado

Lo siguiente no debe describirse como comportamiento implementado en producción:

- Planificación real soportada por LLM
- Participación de Mistral/Qwen en el runtime de producción
- Autoextensión del registry de producción
- Instalación dinámica de paquetes
- Ejecución arbitraria de shell
- Promoción autónoma desde staging a producción

Esos comportamientos no están implementados o solo aparecen documentados como dirección futura en otros documentos.
