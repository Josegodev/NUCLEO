# Planner

## Layer

Verified architecture

## Purpose

Transform an `AgentRequest` into a candidate action.

The planner proposes. It does not authorize, resolve runtime truth, or execute.

## Verified Current Behavior

The deterministic planner strategy currently:

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

### LLM Augmentation

Controlled LLM augmentation is active only when:

```text
request.options.agent_mode == "proposal_only"
```

The production `Planner` is configured with `LLMAssistedPlannerStrategy`.
That strategy asks a proposal provider for model output only in `proposal_only`.
For other requests it uses deterministic fallback.

The LLM output flow is:

```text
raw model output
-> _strip_json_fence(...)
-> json.loads(...)
-> AgentActionProposal shape validation
-> ToolRegistry tool lookup
-> tool payload validation
-> PlannedAction(source="llm_assisted")
```

Accepted LLM output formats are intentionally narrow:

- pure JSON
- JSON wrapped in a fenced Markdown block whose opening fence is empty or
  labelled `json`

Free text mixed with JSON is invalid. A fenced block without a closing fence is
invalid. The code does not extract JSON from narrative text.

Expected proposal shape:

```json
{
  "intent": "string",
  "suggested_action": "echo",
  "arguments": {
    "text": "hola"
  },
  "confidence": 0.9
}
```

`suggested_action` may be `null` if no listed tool fits. In that case,
`arguments` must be `{}` and the result becomes `no_plan`.

#### Tool Schema Injection

`build_tool_contract_prompt(tool_registry)` builds the prompt catalog from the
active `ToolRegistry`:

```text
Available tools and required argument schemas:

- echo
  arguments:
    text: string

- system_info
  arguments:
    {}
```

The catalog is generated from `tool_registry.list_contracts()`. It is not
hardcoded per tool.

Rules given to the model:

- use only listed tools
- use exact argument names
- do not invent fields
- do not use aliases
- if no tool fits, return `suggested_action=null` and `arguments={}`
- output only JSON, optionally wrapped in a `json` fenced block

After parsing, runtime validation still enforces the same contract. For example,
`{"message": "hola"}` is invalid for `echo`; the accepted field is `text`.

#### Fallback

The strategy falls back to deterministic planning when:

- the model provider fails
- JSON normalization fails
- JSON parsing fails
- the proposal shape is invalid
- the tool is unknown or not registered
- the payload does not match the selected tool contract

The fallback plan carries metadata such as `augmentation_attempted`,
`fallback_used`, and `fallback_reason` when available.

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
- Deterministic planning: implemented
- Controlled LLM-assisted planning: implemented for `proposal_only`
- LLM tool execution: not implemented and explicitly prohibited
