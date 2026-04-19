> Archivo origen: `docs/operations/operational_state.md`
> Última sincronización: `2026-04-19`

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

Rama experimental opt-in:

AgentRequest con `experimental_tool_generation=True`  
-> Planner puede emitir `capability_gap_detected`  
-> AgentRuntime gestiona proposal / staging / generación de skeleton  
-> devuelve una respuesta controlada de `capability_gap`  
-> el registry de producción no cambia

## Componentes en operación actual

### API

- aplicación FastAPI
- `POST /agent/run`
- `GET /tools`
- `GET /`

### AgentService

- fachada ligera sobre el runtime
- delega la ejecución con request y execution context

### Runtime

- coordina planner, policy, registry y ejecución de tools
- contiene la ruta actual de manejo de capability gap experimental

### Planner

- basado en reglas
- devuelve contratos implícitos tipo dict
- puede emitir señal experimental de gap solo cuando la request hace opt-in explícito

### PolicyEngine

- deny-by-default sobre nombres de tools de producción
- permite `echo`
- permite `system_info` solo para contexto admin

### Tools de producción

- `echo`
- `system_info`

### Experimental Lab

- ToolProposalService
- ToolGenerationService
- StagingRegistry
- AuditStore
- todo aislado bajo `runtime_lab/`

## Características técnicas verificadas

- `ExecutionContext` forma actualmente parte del pipeline del runtime
- `AgentResponse` expone actualmente `result` estructurado
- el registro de tools de producción ocurre en tiempo de importación dentro del runtime orchestrator
- la salida del planner sigue siendo implícita
- `dry_run` aún no se impone de forma estructural en la ejecución de producción
- la policy de producción no evalúa el payload en profundidad
- las tools experimentales generadas no se auto-registran en producción

## Restricciones operativas

- la ejecución local en una sola máquina es el modelo operativo explícito actual
- las rutas de producción y laboratorio coexisten en el código, pero deben permanecer separadas
- la generación experimental está gated por request, no es comportamiento ambiental
- la simplicidad del runtime sigue siendo prioritaria frente a la expansión agresiva

## Issues abiertos

- no existe un execution plan tipado explícito
- no hay validación completa de payload por tool
- no existe una taxonomía completa de errores estructurados en runtime
- no hay un audit trail integrado para producción
- no existe workflow de promoción a producción para tools generadas en laboratorio
- la semántica de `dry_run` sigue incompleta

## Reglas de trabajo

- mantener estable primero el runtime de producción
- tratar `docs/architecture.md` como fuente de verdad para comportamiento verificado
- tratar `docs/vision/architecture_vision.md` como documento solo de futuro
- tratar el laboratorio experimental como aislado y no productivo por defecto
