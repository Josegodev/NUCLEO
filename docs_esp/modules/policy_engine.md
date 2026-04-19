> Archivo origen: `docs/modules/policy_engine.md`
> Última sincronización: `2026-04-19`

# PolicyEngine

## Capa

Arquitectura verificada

## Propósito

Validar si una ejecución planificada de una tool de producción está permitida antes de llegar a la etapa de ejecución.

## Comportamiento actual verificado

`PolicyEngine.evaluate(...)` actualmente:

- deniega requests no autenticadas
- permite `echo`
- permite `system_info` solo cuando `admin` está presente en los roles
- deniega cualquier otro nombre de tool

Devuelve una `PolicyDecision` con:

- `decision`
- `reason`

## Lo que actualmente no hace

- no evalúa el payload en profundidad
- no impone un `dry_run` con significado real
- no usa `read_only` ni `risk_level`
- no gobierna directamente la generación de artefactos del laboratorio

## Fortalezas

- forma deny-by-default
- separación clara respecto a la ejecución
- el contexto autenticado forma parte del camino de decisión

## Etiqueta de estado

- Autorización de producción: implementada
- Policy sensible a metadatos: no implementada
- Control de promoción del laboratorio: no implementado
