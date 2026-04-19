> Archivo origen: `docs/modules/orchestrator.md`
> Última sincronización: `2026-04-19`

# AgentRuntime

## Capa

Arquitectura verificada

## Propósito

Orquestador central de ejecución del runtime de producción, con una rama aislada mínima para el manejo experimental de capability gaps.

## Comportamiento actual verificado

`AgentRuntime.run(request, context)` actualmente:

1. pide un plan al planner
2. si el plan señala `capability_gap_detected`, deriva a la ruta aislada del laboratorio
3. en caso contrario extrae `tool` y `payload` de producción
4. pide autorización al `PolicyEngine`
5. si la policy deniega, devuelve `blocked`
6. resuelve la tool desde el `ToolRegistry` de producción
7. si falta, devuelve `error`
8. ejecuta `tool.run(payload, context=context)`
9. devuelve `AgentResponse`

## Rama experimental verificada

El runtime compone actualmente servicios de laboratorio en tiempo de importación del módulo y, para requests opt-in, puede:

- crear una proposal
- registrarla en staging
- generar un skeleton de tool
- escribir eventos de audit
- devolver una respuesta controlada de `capability_gap`

Esto no registra la tool en el registry de producción.

## Fortalezas actuales

- pipeline de producción claro
- comprobación explícita de policy antes de ejecutar una tool de producción
- manejo explícito de tool de producción ausente
- la rama experimental permanece aislada del registry de producción

## Limitaciones actuales

- el contrato del planner sigue siendo implícito
- la composición del runtime sigue ocurriendo en tiempo de importación
- el manejo de excepciones es limitado
- `dry_run` aún no se impone de forma estructural para tools de producción
- la respuesta sigue duplicando datos entre `message` y `result`

## Etiqueta de estado

- Ruta de producción: implementada
- Ruta de manejo de gaps en laboratorio: experimental
- Endurecimiento completo de contratos: no implementado
