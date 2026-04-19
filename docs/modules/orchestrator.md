# AgentRuntime

## Layer

Verified architecture

## Purpose

Central execution orchestrator of the production runtime, with a minimal isolated branch for experimental capability-gap handling.

## Verified Current Behavior

`AgentRuntime.run(request, context)` currently:

1. asks the planner for a plan
2. if the plan signals `capability_gap_detected`, routes into the isolated lab flow
3. otherwise extracts production `tool` and `payload`
4. asks `PolicyEngine` for authorization
5. if denied, returns `blocked`
6. resolves the tool from production `ToolRegistry`
7. if missing, returns `error`
8. executes `tool.run(payload, context=context)`
9. returns `AgentResponse`

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

## Current Limitations

- Planner contract still implicit
- Runtime composition still happens at import time
- Limited exception handling
- `dry_run` still not structurally enforced for production tools
- Response still duplicates data between `message` and `result`

## Status Label

- Production path: implemented
- Lab gap-handling path: experimental
- Full contract hardening: not implemented
