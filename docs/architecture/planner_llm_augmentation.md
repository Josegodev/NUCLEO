# Controlled LLM Planner Augmentation

## Current State

NUCLEO production execution remains:

```text
API -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> Tool -> AgentResponse
```

Current safety contracts:

- `Planner` returns a typed `PlannedAction`.
- `PolicyEngine` is the authority for allow or deny decisions.
- `ToolRegistry` is the authority for registered production tools.
- `dry_run=True` never calls `tool.run(...)`.
- `runtime_lab/llm_lab/` remains isolated from production runtime.

This change introduces a design-only augmentation boundary inside Planner. It
does not connect any LLM provider to the production runtime.

## Risks Of Introducing LLM

LLM output is probabilistic, so it must never be treated as runtime truth.

Main risks:

- Free text could be mistaken for an executable plan.
- A model could mention a tool that is unknown or not registered.
- A model could produce a payload that does not match a tool contract.
- A model could appear to bypass `PolicyEngine` if its output is executed directly.
- Auditability could be lost if raw input and raw output are not recorded.

The mitigation is strict separation: LLM can only propose. Planner validates the
proposal. Runtime still sends the resulting `PlannedAction` through
`PolicyEngine`, `ToolRegistry`, and tool input validation.

## PlannerStrategy Design

`PlannerStrategy` is the explicit planning interface:

```text
AgentRequest -> PlannerStrategy.create_plan(...) -> PlannedAction
```

Implemented strategies:

- `DeterministicPlannerStrategy`: current rule-based behavior.
- `LLMAssistedPlannerStrategy`: future stub for LLM-assisted proposals.

Default production behavior remains deterministic because `Planner()` uses
`DeterministicPlannerStrategy` unless another strategy is injected explicitly.

`LLMAssistedPlannerStrategy` does not call a real LLM. It accepts an optional
proposal provider callback for tests or future integration. If disabled, missing,
or invalid, it falls back to deterministic planning.

## Input Contract

The LLM input must always be structured:

```json
{
  "goal": "str",
  "context": ["str"],
  "constraints": ["str"]
}
```

The constraints must state that the LLM:

- returns JSON only
- proposes tools only
- never executes tools
- uses registered tools only
- cannot modify `ToolRegistry`
- cannot bypass `PolicyEngine`

## Output Contract

The LLM output must be valid JSON:

```json
{
  "proposed_plan": [
    {
      "tool_name": "echo",
      "payload": {
        "text": "hola"
      }
    }
  ],
  "justification": "echo was requested",
  "confidence": 0.91
}
```

Free text is invalid. Extra top-level fields are invalid. Extra step fields are
invalid.

Current runtime supports exactly one `PlannedAction`. Therefore multi-step LLM
plans are rejected until the runtime contract is deliberately expanded.

## Required Validations

`LLMPlanOutputValidator` rejects:

- invalid JSON
- output that does not match `LLMPlanProposal`
- unparseable plan steps
- tool names outside the closed tool-name set
- known tool names not present in the active `ToolRegistry`
- payloads that do not match the target tool contract
- multi-step proposals, because current runtime accepts exactly one action

Accepted output is converted to:

```text
PlannedAction(source="llm_assisted")
```

This is still only a proposal. It is not authorization.

## Updated Flow

```text
API
  -> AgentService
  -> AgentRuntime
  -> Planner
       -> deterministic strategy
       -> optional llm_assisted strategy
            -> structured LLM input
            -> raw LLM output
            -> output validation
            -> fallback to deterministic strategy on failure
  -> PolicyEngine
  -> ToolRegistry
  -> Tool
  -> AgentResponse
```

No tool can run from the LLM path directly.

## Traceability

`LLMAssistedPlannerStrategy` records in memory:

- structured input sent to the LLM boundary
- raw output returned by the proposal provider
- validated output when accepted
- acceptance or rejection reason

The current implementation does not persist these records and does not modify
runtime tracing phases.

## Complete Example

Request:

```json
{
  "user_input": "say hola",
  "dry_run": true
}
```

LLM input:

```json
{
  "goal": "say hola",
  "context": [],
  "constraints": [
    "Return valid JSON only.",
    "Propose tools only; never execute tools.",
    "Use registered tools only.",
    "PolicyEngine remains the final authority before execution.",
    "ToolRegistry must not be modified."
  ]
}
```

LLM raw output:

```json
{
  "proposed_plan": [
    {
      "tool_name": "echo",
      "payload": {
        "text": "hola"
      }
    }
  ],
  "justification": "echo was requested",
  "confidence": 0.91
}
```

Validation result:

```text
accepted=true
source=llm_assisted
tool_name=echo
payload={"text": "hola"}
```

Runtime result with `dry_run=true`:

```text
PolicyEngine evaluates first.
ToolRegistry resolves the tool.
Tool input is validated.
tool.run(...) is not called.
```

## Acceptance Criteria

- Deterministic behavior is unchanged when `llm_assisted` is disabled.
- LLM output cannot execute tools.
- LLM output cannot bypass `PolicyEngine`.
- LLM output cannot mutate `ToolRegistry`.
- LLM output is auditable and rejectable before becoming a `PlannedAction`.
