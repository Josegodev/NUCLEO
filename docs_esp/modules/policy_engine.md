> Archivo origen: `docs/modules/policy_engine.md`
> Última sincronización: `2026-04-28`

# PolicyEngine

## Capa

Arquitectura verificada

## Propósito

Validar si una ejecución planificada de una tool de producción está permitida antes de llegar a la etapa de ejecución.

## Comportamiento actual verificado

`PolicyEngine.evaluate(...)` actualmente:

- deniega requests no autenticadas
- permite `echo`
- permite `disk_info`
- permite `system_info` solo cuando `admin` está presente en los roles
- deniega cualquier otro nombre de tool

Devuelve una `PolicyDecision` con:

- `decision`: `PolicyDecisionValue.ALLOW` o `PolicyDecisionValue.DENY`
- `reason`
- `validated_fields`
- `version`

`PolicyDecision` es estricto y rechaza entradas ambiguas:

- `decision` debe ser un enum `PolicyDecisionValue`, no un string libre
- `validated_fields` debe contener valores enum `PolicyValidatedField`
- los campos desconocidos se rechazan con `extra="forbid"`

## Lo que actualmente no hace

- valida la forma del payload contra el contrato de la tool seleccionada
- no toma decisiones diferentes por `dry_run`; el runtime impone la no ejecución
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
