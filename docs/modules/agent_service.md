# AgentService

## Layer

Verified architecture

## Purpose

Provide a stable service-layer facade between API routes and runtime orchestration.

## Verified Current Behavior

`AgentService` currently:

- instantiates `AgentRuntime`
- exposes `run(request, context)`
- delegates execution directly to runtime

It does not currently own:

- planning
- policy
- tool execution
- lab proposal generation logic

## Strengths

- Keeps API thin
- Preserves a stable entrypoint
- Clean place for future tracing or orchestration hooks

## Current Limitations

- Runtime dependency is still constructed directly
- No independent error normalization boundary yet

## Status Label

- Service facade: implemented
- Dependency injection boundary: not implemented
