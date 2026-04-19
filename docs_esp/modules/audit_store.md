> Archivo origen: `docs/modules/audit_store.md`
> Última sincronización: `2026-04-19`

# AuditStore

## Responsabilidad

`AuditStore` persiste eventos simples y estructurados de audit para el workflow experimental de expansión de tools.

## Campos del evento

- event
- timestamp
- proposal_id
- action
- result
- artifact_paths
- metadata

## Salida

Cada evento se escribe como un archivo JSON bajo `runtime_lab/audit/`.

## Notas

- El store es append-only en esta fase.
- Los artefactos de audit soportan review y trazabilidad a posteriori.
