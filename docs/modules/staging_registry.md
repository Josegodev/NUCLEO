# StagingRegistry

## Responsibility

`StagingRegistry` is a JSON-backed isolated registry for experimental proposals.

## Supported statuses

- `draft`
- `generated`
- `reviewed`
- `approved`
- `rejected`

## Persistence

Registry state is stored in `runtime_lab/staging_registry/registry.json`.

## Notes

- This registry is intentionally separate from `app/tools/registry.py`.
- Approval in staging does not imply production activation.
