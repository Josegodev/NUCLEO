# Planner

## Layer

Verified architecture

## Purpose

Transform an `AgentRequest` into a runtime plan or, in the experimental opt-in path, emit a structured capability-gap signal.

## Verified Current Behavior

The planner currently:

1. normalizes `request.user_input` with `strip().lower()`
2. if input contains `system` or `info`, returns a production plan for `system_info`
3. if `experimental_tool_generation=True` and a simple heuristic suggests a missing capability, returns `capability_gap_detected`
4. otherwise returns a production fallback plan for `echo`

## Contract Observed in Code

Current output remains an implicit `dict`.

Observed keys:

- `tool`
- `payload`
- `mode`

Experimental gap path may add:

- `original_input`
- `capability_gap`

## Strengths

- Deterministic
- Side-effect free in production path
- Easy to read
- Experimental branching is explicit and opt-in

## Current Limitations

- Output contract is not typed in production runtime
- Matching logic is weak and heuristic-based
- Capability-gap detection is intentionally simplistic
- Strong coupling to literal production tool names remains

## Status Label

- Production planning: implemented
- Capability-gap signaling: experimental
- Real LLM-assisted planning: not implemented
