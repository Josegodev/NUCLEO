# AgentRuntime

## Layer

Verified architecture

## Purpose

Central execution orchestrator of the production runtime, with a minimal isolated branch for experimental capability-gap handling.

## Verified Current Behavior

`AgentRuntime.run(request, context)` currently:

1. starts an internal in-memory execution trace
2. asks the planner for a plan
3. records the planner step
4. if the plan signals `capability_gap_detected`, routes into the isolated lab flow
5. otherwise extracts production `tool` and `payload`
6. asks `PolicyEngine` for authorization
7. records the policy step
8. if denied, returns `blocked`
9. resolves the tool from production `ToolRegistry`
10. records the registry step
11. if missing, records the registry step as `error` and returns `error`
12. if `dry_run=True`, records a tool step as `skipped` with `executed=False` and does not run the tool
13. otherwise executes `tool.run(payload, context=context)`
14. records success or error for the tool step
15. returns `AgentResponse`

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

## Verified Experimental Branch

The runtime currently composes lab services at module import time and, for opt-in requests, can:

- create a proposal
- register it in staging
- generate a tool skeleton
- write audit events
- return a controlled `capability_gap` response

This does not register the tool in the production registry.

## Current Strengths

- Clear production pipeline
- Explicit policy check before production tool execution
- Explicit handling of missing production tool
- Experimental branch remains isolated from production registry
- Minimal internal trace for planner, policy, registry, and tool stages

## Current Limitations

- Planner contract still implicit
- Runtime composition still happens at import time
- Limited exception handling
- Response still duplicates data between `message` and `result`

## Status Label

- Production path: implemented
- Lab gap-handling path: experimental
- Full contract hardening: not implemented
