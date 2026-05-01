> Archivo origen: `docs/architecture.md`
> Última sincronización: `2026-05-01`

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
-> Tool o proposal dry-run
-> AgentResponse

Flujo de aprobación controlada:

```text
POST /agent/run
-> AgentRuntime.run(...)
-> Planner (determinista + augmentación LLM controlada en proposal_only)
-> PolicyEngine
-> ToolRegistry
-> proposal dry-run persistida por trace_id
-> POST /agent/approve
-> AgentRuntime.approve(...)
-> PolicyEngine
-> ToolRegistry
-> tool.run(...)
-> ApprovalResponse
```

`/agent/approve` no llama al Planner y no llama a ningún proveedor LLM.

## Endpoints verificados

- `GET /` -> respuesta de health
- `GET /tools` -> lista de tools de producción registradas
- `POST /agent/run` -> ejecuta el runtime del agente
- `POST /agent/approve` -> aprueba o rechaza una proposal dry-run persistida

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
- Persiste proposals dry-run de `proposal_only` por `trace_id`
- Aprueba o rechaza proposals persistidas mediante `approve(...)`
- Registra pasos internos de planner, policy, registry y tool mediante el tracer del runtime
- Devuelve un artefacto estructurado `AgentResponse`

### Planner

- Realiza planificación determinista simple basada en reglas
- Puede usar augmentación LLM controlada cuando
  `request.options.agent_mode` es `proposal_only`
- Devuelve un `PlannedAction` tipado y versionado
- No autoriza ni ejecuta tools
- Puede emitir:
  - `planned`
  - `no_plan`

La planificación asistida por LLM acepta solo JSON puro o JSON envuelto en un
fenced block Markdown. El schema aceptado es:

```json
{
  "intent": "string",
  "suggested_action": "echo",
  "arguments": {
    "text": "hola"
  },
  "confidence": 0.9
}
```

`suggested_action` puede ser `null` cuando no encaja ninguna tool registrada.
Todo nombre de tool y payload aceptado se valida contra los contratos activos
de `ToolRegistry`. La salida LLM inválida cae al planner determinista.

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
- Expone contratos registrados mediante `list_contracts()`
- Está separado de staging y de los registries experimentales

### LLM Lab / Ruta lateral experimental

`runtime_lab/llm_lab/` existe dentro del repositorio, pero no forma parte de la
autoridad estable de ejecución. El runtime productivo no llama directamente a
esta capa de laboratorio; la augmentación controlada del Planner usa
`app/adapters/model_router.py`, que reutiliza
`runtime_lab/llm_lab/model_adapter.py` solo como adaptador de proveedor.

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
- `context: dict`
- `options: AgentRunOptions | None`
- `tool: str | None`
- `payload: dict | None`
- `dry_run: bool = True`
- `experimental_tool_generation: bool = False`

`input` se acepta como alias de `user_input`. `AgentRunOptions` contiene
actualmente `backend`, `model_id`, `agent_mode` y `dry_run`. Cuando
`agent_mode=proposal_only`, `dry_run` se fuerza a `true`.

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

### Approval Gate

Las requests de aprobación usan `ApprovalRequest`:

- `trace_id: str`
- `approved: bool`

Las respuestas usan `ApprovalResponse`:

- `status`: `success`, `denied` o `error`
- `trace_id`
- `execution_state`
- `tool`
- `executed`
- `result`
- `reason`

Estados de ejecución:

- `PROPOSED`
- `APPROVED`
- `EXECUTED`
- `REJECTED`
- `DENIED`
- `ERROR`

Invariantes de aprobación:

- la aprobación exige una proposal persistida existente
- `approved=false` marca `REJECTED` y nunca ejecuta
- `approved=true` reconstruye el `PlannedAction` persistido
- la aprobación reevalúa `PolicyEngine` con `dry_run=False`
- la aprobación resuelve de nuevo la tool mediante `ToolRegistry`
- la aprobación valida de nuevo el payload persistido antes de `tool.run(...)`
- una proposal ya `EXECUTED` se devuelve tal cual y no se reejecuta

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

- Garantía de disponibilidad de modelos locales concretos
- Autoextensión del registry de producción
- Instalación dinámica de paquetes
- Ejecución arbitraria de shell
- Promoción autónoma desde staging a producción
- Ejecución multi-step de agentes
- Memoria conversacional

Esos comportamientos no están implementados o solo aparecen documentados como dirección futura en otros documentos.
