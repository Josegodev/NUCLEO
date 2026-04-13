# AgentService

## Purpose
High-level service layer that exposes a stable execution entrypoint for the agent system.

## Real Behavior
`AgentService` instantiates `AgentRuntime` and delegates execution through `run(request)`.
It does not implement planning, policy, tool selection, or transport logic.

## Dependencies
- `AgentRuntime`
- `AgentRequest`
- `AgentResponse`

## Current Strengths
- Clear separation from API routes
- Minimal logic
- Good placeholder for future growth

## Issues Detected
- Direct instantiation of runtime creates tight coupling
- No explicit error normalization
- Type contract depends entirely on runtime correctness
- Documentation is more ambitious than the current implementation

## Risk Level
Medium

## Recommended Improvements
- Allow runtime dependency injection
- Add controlled error boundary
- Keep documentation aligned with actual behavior
- Use this layer as future entrypoint for tracing and execution context

TEST_SAVE_ARCHITECTURE_130426