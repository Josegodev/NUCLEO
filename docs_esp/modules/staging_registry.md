> Archivo origen: `docs/modules/staging_registry.md`
> Última sincronización: `2026-04-19`

# StagingRegistry

## Responsabilidad

`StagingRegistry` es un registry aislado, respaldado por JSON, para proposals experimentales.

## Estados soportados

- `draft`
- `generated`
- `reviewed`
- `approved`
- `rejected`

## Persistencia

El estado del registry se almacena en `runtime_lab/staging_registry/registry.json`.

## Notas

- Este registry está intencionadamente separado de `app/tools/registry.py`.
- La aprobación en staging no implica activación en producción.
