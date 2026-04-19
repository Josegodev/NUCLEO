# AuditStore

## Responsibility

`AuditStore` persists simple structured audit events for the experimental tool-expansion
workflow.

## Event fields

- event
- timestamp
- proposal_id
- action
- result
- artifact_paths
- metadata

## Output

Each event is written as a JSON file under `runtime_lab/audit/`.

## Notes

- The store is append-only at this stage.
- Audit artifacts support review and post-hoc traceability.
