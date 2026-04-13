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

