> Archivo origen: `docs/architecture.md`
> Última sincronización: `2026-04-19`

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
- Devuelve `AgentResponse`

### Planner

- Realiza planificación simple basada en reglas
- Devuelve un `dict` implícito
- Puede emitir:
  - un plan de tool de producción
  - una señal experimental `capability_gap_detected` cuando se solicita explícitamente

### PolicyEngine

- Requiere un `ExecutionContext` autenticado
- Permite `echo`
- Permite `system_info` solo para `admin`
- Deniega cualquier otra tool de producción por nombre

### ToolRegistry

- Almacena instancias de tools de producción en un diccionario
- Resuelve tools por `tool.name`
- Está separado de staging y de los registries experimentales

### Tools de producción

Actualmente registradas en tiempo de importación en el runtime de producción:

- `echo`
- `system_info`

### AgentResponse

El modelo de respuesta actual del runtime contiene:

- `status`
- `message`
- `result` opcional

`message` sigue rellenándose con `str(result)` por compatibilidad hacia atrás.

## Contratos actuales verificados

### AgentRequest

Campos actuales:

- `user_input: str`
- `dry_run: bool = True`
- `experimental_tool_generation: bool = False`

### Salida del Planner

El planner sigue devolviendo un `dict` implícito. El contrato aún no está tipado de forma fuerte en el runtime estable.

Claves observadas:

- `tool`
- `payload`
- `mode`

Cuando se activa la detección experimental de gaps, pueden aparecer claves adicionales:

- `original_input`
- `capability_gap`

### PolicyDecision

Campos actuales:

- `decision`
- `reason`

## Subsistema experimental verificado

Existe un subsistema experimental para propuesta controlada de tools y generación de skeletons, implementado en módulos aislados y en `runtime_lab/`.

### Flujo experimental

Esta ruta es opt-in y no modifica el registry de producción:

AgentRequest con `experimental_tool_generation=True`  
-> Planner puede emitir `capability_gap_detected`  
-> AgentRuntime gestiona el gap  
-> ToolProposalService crea una proposal estructurada  
-> StagingRegistry guarda el estado aislado de staging  
-> ToolGenerationService crea un skeleton solo de laboratorio  
-> AuditStore registra eventos del laboratorio  
-> AgentResponse devuelve un resultado controlado de `capability_gap`

### Regla arquitectónica importante

Las tools experimentales generadas no se auto-registran en el `ToolRegistry` de producción.

## Restricciones y limitaciones verificadas

- La salida del planner sigue siendo implícita y no está validada en runtime
- `dry_run` sigue propagándose, pero no está impuesto de forma estructural para la ejecución de tools de producción
- La policy sigue siendo en gran parte name-based
- Metadatos de tools como `read_only` y `risk_level` aún no se aplican desde policy
- El bootstrap de producción sigue ocurriendo en tiempo de importación en `orchestrator.py`
- El manejo de errores en runtime sigue siendo limitado

## Explícitamente no verificado

Lo siguiente no debe describirse como comportamiento implementado en producción:

- Planificación real soportada por LLM
- Autoextensión del registry de producción
- Instalación dinámica de paquetes
- Ejecución arbitraria de shell
- Promoción autónoma desde staging a producción

Esos comportamientos no están implementados o solo aparecen documentados como dirección futura en otros documentos.
