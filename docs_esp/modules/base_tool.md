> Archivo origen: `docs/modules/base_tool.md`
> Última sincronización: `2026-04-19`

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
- `run(payload, context=None)`

Se espera que las tools concretas implementen `run(...)`.

## Realidad actual importante

- `BaseTool` no es una clase base abstracta estricta
- los metadatos no se validan en tiempo de construcción
- los metadatos aún no se aplican desde policy
- los contratos de entrada/salida siguen siendo implícitos

## Etiqueta de estado

- Concepto común de contrato de tool: implementado
- Enforcement fuerte de contratos tipados: no implementado
