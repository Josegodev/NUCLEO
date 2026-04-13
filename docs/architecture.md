## Verified Current Behavior

### Execution Flow (actual)

AgentRequest
→ Planner (`create_plan`)
→ PolicyEngine (`evaluate`)
→ ToolRegistry (`get`)
→ Tool (`run`)
→ AgentResponse

### Current Implementation Characteristics

- Planner returns a plain `dict` with keys:
  - `tool`: str
  - `payload`: dict  
  This contract is implicit and not validated by the runtime.

- PolicyEngine applies a static whitelist based only on `tool_name`:
  - allows: `echo`, `system_info`
  - denies all others  
  It does not evaluate `payload` or `dry_run`.

- `dry_run` is passed through the system but:
  - does not affect policy decisions
  - does not prevent tool execution  
  Tools are still executed normally by the runtime.

- Tool resolution is performed via `ToolRegistry.get(tool_name)`:
  - returns a tool instance or `None`
  - missing tools are handled explicitly by the runtime

- Tool results are returned via:
  ```python
  message = str(result)

  # Authentication and ExecutionContext architecture

## Objective
Introduce authentication without coupling identity to the runtime process, and make execution identity available across the full pipeline.

## Chosen design
Request-scoped API key authentication with `ExecutionContext`.

## Why this design
The system must scale beyond local single-user execution.
Authentication must belong to each request, not to the uvicorn process.

## Architectural rule
Authentication is handled at the API boundary.
Authorization is handled by policy.
Execution uses `ExecutionContext`.
Tools do not validate credentials.

## Layer responsibilities

### API
- receive HTTP request
- validate API key
- build `ExecutionContext`

### Service
- propagate request + context
- no auth logic

### Runtime
- orchestrate execution
- pass context to policy and tools

### Policy
- authorize by user / role / tool

### Tool
- execute using payload + context
- no auth / no permission logic

## Current auth mode
- API key via FastAPI `HTTPBearer`
- suitable for local/dev bootstrap and internal API use

## Future migration path
Authentication mechanism may later evolve to JWT.
This should not require redesign of:
- `AgentService`
- `AgentRuntime`
- `PolicyEngine`
- `BaseTool`

Only the auth boundary should change.

## Stable internal contract
`ExecutionContext` is now part of the execution pipeline and should remain the standard carrier for:
- user identity
- roles
- auth method
- request id
- trace metadata

## Next architecture step
Refactor `AgentResponse` to structured output instead of stringified tool results.

