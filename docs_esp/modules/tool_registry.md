> Archivo origen: `docs/modules/tool_registry.md`
> Última sincronización: `2026-04-19`

# ToolRegistry

## Capa

Arquitectura verificada

## Propósito

Resolver tools de producción por nombre desde el registry actual de producción en memoria.

## Comportamiento actual verificado

`ToolRegistry` almacena instancias de tools en un diccionario indexado por `tool.name`.

Operaciones soportadas:

- `register(tool)`
- `get(tool_name)`
- `list_tools()`

## Distinción importante

Este registry es el registry de producción. Está separado de:

- `runtime_lab/`
- staging registry
- proposal store
- skeletons de tools generadas

Las tools del laboratorio no se auto-registran aquí.

## Limitaciones actuales

- los nombres duplicados sobrescriben silenciosamente
- el contrato de tool no se valida de forma fuerte en el momento del registro
- la mutación en runtime y la mutación en bootstrap no están claramente separadas

## Etiqueta de estado

- Registry de producción: implementado
- Integración con staging / promoción: no implementada en el registry de producción
