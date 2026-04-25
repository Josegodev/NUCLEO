> Archivo origen: `docs/modules/planner.md`
> Última sincronización: `2026-04-25`

# Planner

## Capa

Arquitectura verificada

## Propósito

Transformar un `AgentRequest` en una acción candidata determinista.

El planner propone. No autoriza, no resuelve la verdad de runtime y no ejecuta.

## Comportamiento actual verificado

El planner actualmente:

1. normaliza `request.user_input` con `strip().lower()`
2. si `request.tool` está definido y la tool existe en `ToolRegistry`, devuelve `planned`
3. evalúa una pequeña tabla explícita de reglas deterministas
4. si una regla encaja y su tool existe en `ToolRegistry`, devuelve `planned`
5. si no, devuelve `no_plan`

## Contrato observado en código

La salida actual es `PlannedAction`.

Campos:

- `status`
- `tool_name`
- `payload`
- `confidence`
- `reason`
- `source`

Estados:

- `planned`
- `no_plan`

`no_plan` es esperado cuando ninguna regla determinista encaja.

## Fortalezas

- determinista
- sin efectos laterales en la ruta de producción
- fácil de leer
- las reglas están en una tabla explícita y auditable
- comprueba que las tools objetivo existen en `ToolRegistry`
- el runtime recibe un contrato tipado en lugar de un dict implícito

## Limitaciones actuales

- la lógica de matching es débil y basada en heurísticas
- persiste un acoplamiento fuerte a nombres literales de tools de producción

## Etiqueta de estado

- Planificación de producción: implementada
- Planificación real asistida por LLM: no implementada
