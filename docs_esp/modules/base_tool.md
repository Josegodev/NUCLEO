> Archivo origen: `docs/modules/base_tool.md`
> Última sincronización: `2026-04-28`

# BaseTool

## Capa

Arquitectura verificada

## Propósito

Definir la interfaz conceptual común para las tools de producción.

## Comportamiento actual verificado

`BaseTool` actualmente declara:

- `name`
- `description`
- `read_only`
- `risk_level`
- `contract`
- `validate_input(payload)`
- `validate_output(output)`
- `run(payload, context=None)`

Se espera que las tools concretas implementen `run(...)`.

`contract` debe ser un `ToolContractArtifact` e incluye:

- nombre de tool
- schema de entrada
- schema de salida
- precondiciones
- postcondiciones
- efectos secundarios explícitos
- versión

## Realidad actual importante

- `BaseTool` no es una clase base abstracta estricta
- los metadatos no se validan en tiempo de construcción
- los metadatos aún no se aplican desde policy
- los contratos de entrada/salida son explícitos para las tools de producción registradas

## Etiqueta de estado

- Concepto común de contrato de tool: implementado
- Enforcement fuerte en la frontera registry/runtime: implementado
