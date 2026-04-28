> Archivo origen: `docs/modules/tool_registry.md`
> Última sincronización: `2026-04-28`

# ToolRegistry

## Capa

Arquitectura verificada

## Propósito

Resolver tools de producción por nombre desde el registry actual de producción en memoria.

## Comportamiento actual verificado

`ToolRegistry` almacena instancias de tools de producción indexadas por
`tool.name`, pero ya no es solo un diccionario sin comprobaciones. El registro
valida la tool contra la frontera contractual de producción.

Operaciones soportadas:

- `register(tool)`
- `get(tool_name)`
- `list_tools()`
- `list_contracts()`

El registro exige:

- que el objeto herede de `BaseTool`
- que el nombre esté dentro del conjunto cerrado de tools de producción
- que la tool exponga un `ToolContractArtifact`
- que el nombre del contrato coincida con `tool.name`
- que el nombre no esté ya registrado

## Distinción importante

Este registry es el registry de producción. Está separado de:

- `runtime_lab/`
- staging registry
- proposal store
- skeletons de tools generadas

Las tools del laboratorio no se auto-registran aquí.

## Limitaciones actuales

- la mutación en runtime y la mutación en bootstrap no están claramente separadas

## Etiqueta de estado

- Registry de producción con validación de contrato: implementado
- Integración con staging / promoción: no implementada en el registry de producción
