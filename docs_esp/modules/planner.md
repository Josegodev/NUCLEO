> Archivo origen: `docs/modules/planner.md`
> Última sincronización: `2026-04-19`

# Planner

## Capa

Arquitectura verificada

## Propósito

Transformar un `AgentRequest` en un plan de runtime o, en la ruta experimental opt-in, emitir una señal estructurada de capability gap.

## Comportamiento actual verificado

El planner actualmente:

1. normaliza `request.user_input` con `strip().lower()`
2. si la entrada contiene `system` o `info`, devuelve un plan de producción para `system_info`
3. si `experimental_tool_generation=True` y una heurística simple sugiere que falta una capacidad, devuelve `capability_gap_detected`
4. en cualquier otro caso devuelve un plan fallback de producción para `echo`

## Contrato observado en código

La salida actual sigue siendo un `dict` implícito.

Claves observadas:

- `tool`
- `payload`
- `mode`

La ruta experimental de gap puede añadir:

- `original_input`
- `capability_gap`

## Fortalezas

- determinista
- sin efectos laterales en la ruta de producción
- fácil de leer
- la ramificación experimental es explícita y opt-in

## Limitaciones actuales

- el contrato de salida no está tipado en el runtime de producción
- la lógica de matching es débil y basada en heurísticas
- la detección de capability gap es intencionadamente simple
- persiste un acoplamiento fuerte a nombres literales de tools de producción

## Etiqueta de estado

- Planificación de producción: implementada
- Señalización de capability gap: experimental
- Planificación real asistida por LLM: no implementada
