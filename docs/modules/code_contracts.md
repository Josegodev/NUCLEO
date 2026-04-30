# Code Contracts

## Scope

This document summarizes the current Python contracts used by the production
runtime. It is documentation only. It does not introduce new architecture,
runtime behavior, tools, or LLM integration.

Evidence source: `outputs/audits/docs_contracts_audit.md`.

## AgentRequest

Defined in `app/schemas/requests.py`.

Current fields:

- `user_input: str | None`
- `tool: str | None`
- `payload: dict[str, Any] | None`
- `dry_run: bool = True`
- `experimental_tool_generation: bool = False`

Contract:

- The request may be natural-language-like through `user_input`.
- The request may be explicit through `tool` plus `payload`.
- `dry_run` defaults to `True`.
- `experimental_tool_generation` is a request flag, not permission to register
  or execute generated tools in production.

## AgentResponse

Defined in `app/schemas/responses.py`.

Current fields:

- `status: ExecutionStatus`
- `result: dict[str, JsonValue] | None`
- `errors: list[ExecutionError]`
- `trace_id: str`
- `version: "execution_result.v1"`

Contract:

- `status` is closed to `success`, `error`, or `rejected`.
- `errors` contains structured `ExecutionError` items.
- A successful response must not include errors.
- A non-success response must include at least one error.
- Extra fields are forbidden.

## ExecutionContext

Defined in `app/schemas/context.py`.

Current fields:

- `user_id`
- `username`
- `roles`
- `authenticated`
- `auth_method`
- `request_id`
- `idempotency_key`
- `api_key_name`
- `client_ip`

Contract:

- The API/auth boundary builds the context.
- Runtime passes the context to policy and tools.
- Policy uses the context for authentication and role checks.
- Tools receive context for execution metadata, not for authorization decisions.

## Planner And PlannedAction

`Planner` is defined in `app/runtime/planner.py`.
`PlannedAction` is defined in `app/schemas/execution.py`.

Contract:

- `Planner.create_plan(request)` must return `PlannedAction`.
- The planner is deterministic and rule-based.
- The planner does not execute tools.
- The planner does not authorize execution.
- The planner must not invent unavailable tools.

`PlannedAction` fields:

- `tool_name: ToolName | None`
- `payload: dict[str, JsonValue]`
- `status: "planned" | "no_plan"`
- `confidence: float`
- `reason: str`
- `source`
- `preconditions`
- `expected_output`
- `version: "action.v1"`

Closed behavior:

- `status="planned"` requires `tool_name`.
- `status="no_plan"` must not include `tool_name`, preconditions, or expected
  output.
- Planned payloads are validated against the selected tool contract.

## PolicyDecision And PolicyDecisionValue

Defined in `app/policies/models.py`.

Contract:

- `PolicyDecision.decision` must be `PolicyDecisionValue.ALLOW` or
  `PolicyDecisionValue.DENY`, not free strings.
- `PolicyDecision` is strict and forbids extra fields.
- `reason` is required and must be non-empty.
- `validated_fields` must contain at least one `PolicyValidatedField`.
- `version` is fixed to `"policy_decision.v1"`.

Current decision values:

- `PolicyDecisionValue.ALLOW`
- `PolicyDecisionValue.DENY`

## ToolRegistry

Defined in `app/tools/registry.py`.

Contract:

- `register(tool)` accepts only `BaseTool` instances.
- Each registered tool must expose a `ToolContractArtifact`.
- Tool names must belong to the closed production tool set.
- `contract.name` must match `tool.name`.
- Duplicate tool names are rejected.
- `get(tool_name)` returns a tool instance or `None`.
- `list_tools()` returns registered production tool instances.
- `list_contracts()` returns their tool contracts.

Current production tool names:

- `echo`
- `disk_info`
- `system_info`

## BaseTool And ToolResult

`BaseTool` is defined in `app/tools/base.py`.
`ToolResult` is defined in `app/schemas/execution.py`.

`BaseTool` contract:

- Tools expose `name`, `description`, `read_only`, `risk_level`, and
  `contract`.
- `validate_input(payload)` validates payload through the registered tool
  schema.
- `validate_output(output)` validates output through the registered tool
  schema.
- `run(payload, context)` is the execution boundary.
- Tools do not authenticate or authorize themselves; policy runs before tool
  execution.

`ToolResult` fields:

- `tool_name`
- `output`
- `success`

Current runtime behavior:

- The runtime validates concrete tool output with `tool.validate_output(...)`.
- The validated output dictionary is placed in `AgentResponse.result`.
- `ToolResult` exists as a schema artifact, but the public response contract is
  `AgentResponse`.

## dry_run

Contract:

- `dry_run=True` validates planning, policy, registry, and tracing, but does
  not call `tool.run(...)`.
- Runtime still creates a trace.
- Runtime still records planner, policy, registry, and skipped tool steps when
  those stages are reached.
- Runtime still validates the selected tool input before returning the dry-run
  result.
- The dry-run result includes `dry_run=True`, `executed=False`, `tool`, and
  validated `payload`.

This means `dry_run=True` is not a shortcut around policy or registry checks.
It is a non-executing runtime path.

## Tracing

Defined in `app/runtime/tracing.py`.

Contract:

- Tracing is internal and in-memory.
- Tracing does not persist data.
- Tracing does not call external services.
- Tracing does not decide whether tools may run.
- Trace phases are closed to `planner`, `policy`, `registry`, and `tool`.
- Trace statuses are closed to `success`, `error`, `denied`, and `skipped`.
- Runtime returns `trace_id` through `AgentResponse`.
