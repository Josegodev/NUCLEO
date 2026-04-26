> Archivo origen: `docs/operations/operational_state.md`
> Última sincronización: `2026-04-26`

# Estado operativo - NUCLEO

## Propósito

Describir el estado operativo actual del sistema usando solo comportamiento verificado en código o implicado directamente por la estructura del repositorio.

## Objetivo actual

Operar un runtime agentic modular, mínimo y controlado sobre FastAPI, manteniendo la ruta de ejecución de producción comprensible y aislada de las capacidades experimentales de laboratorio.

## Arquitectura actual verificada

Flujo de producción:

AgentRequest  
-> AgentService  
-> AgentRuntime  
-> Planner  
-> PolicyEngine  
-> ToolRegistry  
-> Tool  
-> AgentResponse

## Componentes en operación actual

### API

- aplicación FastAPI
- `POST /agent/run`
- `POST /agent/run` acepta `X-Idempotency-Key` opcional
- `GET /tools`
- `GET /`

### AgentService

- fachada ligera sobre el runtime
- delega la ejecución con request y execution context

### Runtime

- coordina planner, policy, registry y ejecución de tools
- evalúa policy antes de resolver la instancia ejecutable de la tool
- valida la salida del planner antes de policy, registry o ejecución de tools
- devuelve `no_plan` sin ejecutar tools cuando el planner no encuentra una coincidencia determinista

### Planner

- basado en reglas
- usa una pequeña tabla explícita de reglas deterministas
- devuelve `PlannedAction` tipado
- emite `planned` o `no_plan`
- no autoriza ni ejecuta tools

### PolicyEngine

- deny-by-default sobre nombres de tools de producción
- permite `echo`
- permite `disk_info`
- permite `system_info` solo para contexto admin

### Tools de producción

- `echo`
- `system_info`
- `disk_info`

### Experimental Lab

- ToolProposalService
- ToolGenerationService
- StagingRegistry
- AuditStore
- todo aislado bajo `runtime_lab/`

### LLM Lab / Ruta lateral experimental

`runtime_lab/llm_lab/` existe dentro del repositorio, pero es una ruta lateral
experimental de observación. No forma parte del runtime de producción.

Propósito:

- cargar contexto de NUCLEO para preguntas externas o locales
- ejecutar chats locales de Mistral/Qwen mediante Ollama
- mantener memoria local de chat en SQLite bajo `runtime_lab/llm_lab/`
- generar informes de revisión HARDENING bajo `runtime_lab/llm_lab/reports/`

Integración actual con el runtime:

- ninguna
- no llama a `AgentService`
- no llama a `AgentRuntime`
- no interactúa con `Planner`, `PolicyEngine`, `ToolRegistry` ni `Tools` de
  producción

Permisos:

- leer contexto del repositorio
- escribir informes y memoria SQLite solo dentro del laboratorio
- observar y resumir

Acciones prohibidas:

- ejecutar tools de producción
- modificar policy
- llamar automáticamente a `/agent/run`
- actuar como Planner
- registrar tools en el `ToolRegistry` de producción

Script relacionado de exportación de contexto:

- `scripts/export_nucleo_context.py` lee `README.md`,
  `docs/architecture.md`, `docs/operations/operational_state.md`,
  `docs/operations/session_log.md` y `docs/modules/*.md`
- escribe `llm_context/nucleo_context_snapshot.md` y
  `llm_context/nucleo_context_snapshot.json`
- no debe importar ni llamar a `AgentService`, `AgentRuntime`, `Planner`,
  `PolicyEngine`, `ToolRegistry` ni `Tools`

## Características técnicas verificadas

- `ExecutionContext` forma actualmente parte del pipeline del runtime
- `AgentResponse` expone actualmente `result` estructurado
- el registro de tools de producción ocurre en el registry de producción
- la salida del planner está tipada como `PlannedAction`
- `dry_run` se impone de forma estructural: las tools no se ejecutan
- la policy de producción no evalúa el payload en profundidad
- las tools experimentales generadas no se auto-registran en producción
- Mistral/Qwen no forman parte del flujo de ejecución de producción
- la idempotencia de `POST /agent/run` se gestiona en el borde API, antes de que
  `AgentService` delegue en `AgentRuntime`

## Contrato de idempotencia de `/agent/run`

- Sin `X-Idempotency-Key`, `/agent/run` conserva el comportamiento existente y
  delega cada request en `AgentService`.
- Con un `X-Idempotency-Key` no vacío de 128 caracteres como máximo, el primer
  request almacena la `AgentResponse` devuelta en memoria del proceso.
- Un reintento con el mismo principal autenticado y la misma clave de idempotencia
  devuelve la `AgentResponse` cacheada sin llamar otra vez a `AgentRuntime`.
- El cache es local al proceso Python actual. No usa Redis, no se comparte entre
  workers y se pierde al reiniciar el proceso.
- La idempotencia no está implementada dentro de `AgentRuntime`, `Planner`,
  `PolicyEngine`, `ToolRegistry` ni tools.

## Restricciones operativas

- la ejecución local en una sola máquina es el modelo operativo explícito actual
- las rutas de producción y laboratorio coexisten en el código, pero deben permanecer separadas
- los servicios de generación experimental existen como código aislado y no
  están conectados al flujo estable de `/agent/run`
- la simplicidad del runtime sigue siendo prioritaria frente a la expansión agresiva

## Issues abiertos

- no hay validación completa de payload por tool
- no existe una taxonomía completa de errores estructurados en runtime
- la traza del runtime está en memoria y no se expone por API
- no existe workflow de promoción a producción para tools generadas en laboratorio
- mezclar salidas de `llm_lab` con decisiones del runtime rompería el límite
  determinista actual

## Reglas de trabajo

- mantener estable primero el runtime de producción
- tratar `docs/architecture.md` como fuente de verdad para comportamiento verificado
- tratar `docs/vision/architecture_vision.md` como documento solo de futuro
- tratar el laboratorio experimental como aislado y no productivo por defecto
