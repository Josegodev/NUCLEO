# Planner

## Layer

Verified architecture

## Purpose

Transform an `AgentRequest` into a deterministic candidate action.

The planner proposes. It does not authorize, resolve runtime truth, or execute.

## Verified Current Behavior

The planner currently:

1. normalizes `request.user_input` with `strip().lower()`
2. if `request.tool` is set and the tool exists in `ToolRegistry`, returns `planned`
3. evaluates a small explicit table of deterministic rules
4. if a rule matches and its tool exists in `ToolRegistry`, returns `planned`
5. otherwise returns `no_plan`

## Contract Observed in Code

Current output is `PlannedAction`.

Fields:

- `status`
- `tool_name`
- `payload`
- `confidence`
- `reason`
- `source`

Statuses:

- `planned`
- `no_plan`

`no_plan` is expected when no deterministic rule matches.

## Strengths

- Deterministic
- Side-effect free in production path
- Easy to read
- Rules are table-driven and auditable
- Planner checks rule targets against `ToolRegistry`
- Runtime receives a typed contract instead of an implicit dict

## Current Limitations

- Matching logic is weak and heuristic-based
- Strong coupling to literal production tool names remains

## Status Label

- Production planning: implemented
- Real LLM-assisted planning: not implemented
