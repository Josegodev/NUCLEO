# ToolProposalService

## Responsibility

`ToolProposalService` creates deterministic experimental proposals from an
explicit caller-provided proposal request. The current stable Planner does not
call this service and does not emit `capability_gap_detected`.

The current version does not call a real LLM; it acts as a stable placeholder
that emits structured proposal JSON.

## Output

The service writes proposal artifacts to `runtime_lab/proposals/<proposal_id>.json`.

## Notes

- The proposal is descriptive, not executable.
- Proposal generation is audited.
- The service is isolated from the production registry.
- It is not connected to the stable `/agent/run` flow.
