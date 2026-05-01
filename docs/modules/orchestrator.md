# AgentRuntime

## Layer

Verified architecture

## Purpose

Central execution orchestrator of the production runtime.

## Verified Current Behavior

`AgentRuntime.run(request, context)` currently:

1. starts an internal in-memory execution trace
2. asks the planner for a `PlannedAction`
3. records the planner step
4. validates that the planner returned a versioned `PlannedAction`
5. if the plan is `no_plan`, returns a structured `rejected` response
6. otherwise extracts candidate `tool_name` and `payload`
7. asks `PolicyEngine` for authorization
8. records the policy step
9. if denied, returns structured `rejected`
10. resolves the tool from production `ToolRegistry`
11. records the registry step
12. if missing, records the registry step as `error` and returns structured `error`
13. validates the planned payload against the selected tool contract
14. if `dry_run=True`, records a tool step as `skipped` with `executed=False` and does not run the tool
15. if `request.options.agent_mode == "proposal_only"`, persists the proposal by `trace_id`
16. otherwise executes `tool.run(payload, context=context)`
17. validates the tool output against the selected tool contract
18. records success or error for the tool step
19. returns `AgentResponse`

The runtime executes a tool only after a valid action artifact and
`PolicyDecisionValue.ALLOW`. `dry_run=True` never calls `tool.run(...)`.

## Proposal Mode

When `agent_mode="proposal_only"` and `dry_run=True`, the runtime returns a
proposal result instead of executing:

```text
executed=false
execution_allowed=false
execution_state=PROPOSED
```

The proposal is persisted through `ApprovalStore` using the response
`trace_id`. The persisted record includes:

- `trace_id`
- `user_input`
- `planned_action`
- `proposed_tool`
- `arguments`
- `policy_decision_initial`
- `created_at`
- `execution_state`

This persistence is internal runtime state. The frontend does not store or edit
the executable payload.

## Approval Gate

`AgentRuntime.approve(trace_id, approved, context)` implements controlled
execution for persisted proposals.

If `approved=false`:

- a `PROPOSED` record moves to `REJECTED`
- no planner call is made
- no LLM call is made
- no tool is executed

If `approved=true`:

- the runtime loads the proposal by `trace_id`
- reconstructs the persisted `PlannedAction`
- does not call Planner
- does not call any LLM provider
- re-evaluates `PolicyEngine` with `dry_run=False`
- resolves the tool again through `ToolRegistry`
- validates the persisted payload again with `tool.validate_input(...)`
- executes `tool.run(...)` only after those checks pass

Execution states used by the gate:

- `PROPOSED`
- `APPROVED`
- `EXECUTED`
- `REJECTED`
- `DENIED`
- `ERROR`

Idempotency rule:

- if a proposal is already `EXECUTED`, a second approval returns the existing
  state and does not call `tool.run(...)` again

`/agent/approve` does not accept `tool_name` or payload from the client. The
only executable payload is the one persisted from the original dry-run proposal.

Public `AgentResponse.status` is closed to:

- `success`
- `error`
- `rejected`

Breaking change: `AgentResponse.message` is no longer part of the public
contract. The execution-result artifact uses `status`, `result`, `errors`,
`trace_id`, and `version`.

## Internal Trace Contract

Tracing is implemented in `app/runtime/tracing.py` and is intentionally
in-memory only.

`ExecutionTrace`:

- `trace_id`
- `request_id`
- `steps`

`ExecutionStep`:

- `step_id`
- `phase`: `planner`, `policy`, `registry`, or `tool`
- `input`
- `output`
- `status`: `success`, `denied`, `error`, or `skipped`
- `error`
- `timestamp`

Tracer failures are isolated from authorization and execution decisions. A
tracing failure must not cause a denied tool to execute and must not hide a real
tool error.

## Current Strengths

- Clear production pipeline
- Explicit policy check before production tool execution
- Explicit handling of missing production tool
- Explicit proposal -> approval -> execution transition
- Idempotent approval for already executed proposals
- Minimal internal trace for planner, policy, registry, and tool stages

## Current Limitations

- Runtime composition still happens at import time
- Runtime trace remains in-memory only

## Status Label

- Production path: implemented
- Artifact contract hardening: implemented for current production tools
- Approval Gate: implemented
