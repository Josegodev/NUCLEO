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
4. validates that the planner returned `PlannedAction`
5. if the plan is `no_plan`, returns a controlled `no_plan` response
6. otherwise extracts candidate `tool_name` and `payload`
7. resolves the tool from production `ToolRegistry`
8. records the registry step
9. if missing, records the registry step as `error` and returns `error`
10. asks `PolicyEngine` for authorization
11. records the policy step
12. if denied, returns `blocked`
14. if `dry_run=True`, records a tool step as `skipped` with `executed=False` and does not run the tool
15. otherwise executes `tool.run(payload, context=context)`
16. records success or error for the tool step
17. returns `AgentResponse`

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
- Minimal internal trace for planner, policy, registry, and tool stages

## Current Limitations

- Runtime composition still happens at import time
- Limited exception handling
- Response still duplicates data between `message` and `result`

## Status Label

- Production path: implemented
- Full contract hardening: not implemented
