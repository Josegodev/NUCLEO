> Archivo origen: `docs/modules/tool_proposal_service.md`
> Última sincronización: `2026-04-19`

# ToolProposalService

## Responsabilidad

`ToolProposalService` crea proposals experimentales deterministas cuando el planner detecta un capability gap. La versión actual no invoca un LLM real; actúa como placeholder estable que emite JSON estructurado de proposal.

## Salida

El servicio escribe artefactos de proposal en `runtime_lab/proposals/<proposal_id>.json`.

## Notas

- La proposal es descriptiva, no ejecutable.
- La generación de proposals queda auditada.
- El servicio está aislado del registry de producción.
