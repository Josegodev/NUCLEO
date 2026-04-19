# ToolProposalService

## Responsibility

`ToolProposalService` creates deterministic experimental proposals when the planner
detects a capability gap. The current version does not call a real LLM; it acts as a
stable placeholder that emits structured proposal JSON.

## Output

The service writes proposal artifacts to `runtime_lab/proposals/<proposal_id>.json`.

## Notes

- The proposal is descriptive, not executable.
- Proposal generation is audited.
- The service is isolated from the production registry.
