> Archivo origen: `docs/EVOLUTION_MAP.md`
> Última sincronización: `2026-04-19`

# Mapa de evolución

## Propósito

Este documento traza la transición desde el estado actualmente verificado del sistema hacia un runtime más robusto, distinguiendo con claridad entre capacidades implementadas, parciales, experimentales y futuras.

## Estado actual verificado

El repositorio ofrece actualmente:

- entrypoint FastAPI para ejecución del runtime
- `AgentService` como fachada sobre `AgentRuntime`
- `AgentRuntime` como orquestador de producción
- `Planner` basado en reglas
- `PolicyEngine` name-based con comprobación de rol para `system_info`
- `ToolRegistry` para resolución de tools de producción
- tools de producción:
  - `echo`
  - `system_info`
- `ExecutionContext` propagado a través de API, runtime, policy y tools
- `AgentResponse` con `status`, `message` y `result` opcional

## Estado experimental actual

El repositorio también contiene un subsistema experimental de laboratorio aislado:

- señal de capability gap desde el planner cuando se solicita explícitamente
- placeholder determinista para generación de proposals
- staging registry aislado
- generación de skeletons solo de laboratorio
- generación de artefactos de audit

Este subsistema está implementado, pero no forma parte de la ruta estable del registry de producción.

## Principales debilidades pendientes

### 1. Contratos internos débiles

- la salida del planner sigue siendo implícita
- los contratos de payload de las tools siguen siendo implícitos
- la salida de las tools aún no está estandarizada más allá del contenedor actual de respuesta

### 2. Control de ejecución incompleto

- `dry_run` sigue sin imponerse de forma estructural en producción
- la policy no evalúa el payload en profundidad
- los metadatos `read_only` y `risk_level` aún no se aplican desde policy

### 3. Gaps de robustez del runtime

- manejo limitado de excepciones estructuradas en runtime
- no existe una taxonomía formal de errores de dominio

### 4. Acoplamiento de bootstrap

- planner, policy engine, registry y servicios experimentales siguen componiéndose en tiempo de importación del módulo

### 5. Riesgo de deriva documental y operativa

- los documentos históricos contienen snapshots anteriores y deben leerse como logs, no como verdad actual
- `docs_esp/` es ahora una traducción mantenida de `docs/`, pero `docs/` sigue siendo la fuente primaria verificada

## Prioridades de evolución

### Prioridad 1 - Reforzar contratos

- introducir un execution plan tipado
- definir contratos estructurados de payload para tools
- definir contratos más sólidos para resultados de tools
- reforzar el contrato de `BaseTool`

### Prioridad 2 - Imponer control de ejecución

- hacer que `dry_run` tenga efecto real
- usar metadatos de tools en decisiones de policy
- preparar comprobaciones de policy sensibles al payload

### Prioridad 3 - Mejorar la robustez del runtime

- añadir manejo controlado de errores por etapa del pipeline
- estandarizar respuestas de error de dominio
- mejorar la trazabilidad

### Prioridad 4 - Desacoplar composición y orquestación

- inyectar planner, registry y policy en el runtime
- mover la composición de producción y del laboratorio a una capa de bootstrap dedicada

### Prioridad 5 - Madurar el laboratorio experimental

- workflow real de review para el staging registry
- metadatos más ricos en artefactos
- proceso explícito de promoción
- integración real con LLM solo detrás de límites controlados

## Aún no recomendado

Lo siguiente no debe tratarse todavía como prioridad de producción antes de reforzar contratos y control de ejecución:

- activación autónoma de tools
- autoextensión de producción
- autoridad no controlada del planner soportado por LLM
- ejecución distribuida
- orquestación implícita de memoria/estado

## Resultado objetivo

Un runtime con:

- contratos explícitos
- ejecución controlada
- registry de producción estable
- laboratorio experimental aislado
- orquestación trazable
- documentación que separe con claridad el estado actual de la visión futura
