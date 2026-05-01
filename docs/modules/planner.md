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

## Planner Contract - HARDENING

The planner contract is closed around one responsibility:

```text
AgentRequest -> PlannerStrategy -> PlannedAction
```

`PlannerStrategy` receives an `AgentRequest` and must return a valid
`PlannedAction`. The public `Planner` wrapper checks this boundary before
returning the plan to `AgentRuntime`.

The only valid production execution order remains:

```text
Planner -> PolicyEngine -> ToolRegistry -> Tool
```

Allowed behavior:

- `DeterministicPlannerStrategy` may inspect `AgentRequest` and produce a
  deterministic `PlannedAction`.
- `LLMAssistedPlannerStrategy` may build structured LLM input, receive raw LLM
  output from an injected proposal provider, validate that output, and fall back
  to deterministic planning when validation fails.
- `LLMAssistedPlannerStrategy` may convert validated output to
  `PlannedAction(source="llm_assisted")`.
- LLM augmentation audit records may store raw output, validated output,
  acceptance state, and fallback reason.

Explicitly prohibited behavior:

- `LLM -> Tool`
- `LLM -> PolicyDecision`
- `LLM -> ToolRegistry`
- Planner strategies must not execute tools.
- Planner strategies must not create or return `PolicyDecision`.
- Planner strategies must not register tools.
- Planner strategies must not bypass `PolicyEngine`.

Validation requirements for LLM-assisted planning:

- invalid JSON is rejected
- unknown tools are rejected
- tools missing from the active `ToolRegistry` are rejected
- invalid payloads are rejected
- incomplete outputs are rejected
- rejected LLM output triggers deterministic fallback

Authority remains outside the planner:

- `PolicyDecisionValue = ALLOW | DENY`
- `dry_run` is a runtime execution flag, not a `PolicyDecisionValue`
- tools execute only after `PolicyEngine` returns `ALLOW`

## Status Label

- Production planning: implemented
- Real LLM execution/integration: not implemented
- LLM-assisted planning boundary: stubbed, validated, and disabled unless
  explicitly injected
