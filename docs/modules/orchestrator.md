# AgentRuntime

## Purpose
Central execution orchestrator of the modular agent runtime.

## Real Behavior
The runtime receives an `AgentRequest`, asks the planner for a plan, evaluates policy, resolves the requested tool from the registry, executes it, and returns an `AgentResponse`.

Current execution flow:
1. `planner.create_plan(request)`
2. Extract `plan["tool"]` and `plan["payload"]`
3. `policy_engine.evaluate(tool_name, payload, dry_run)`
4. If denied, return `blocked`
5. Resolve tool from registry
6. If missing, return `error`
7. Execute `tool.run(payload)`
8. Return `success` or `dry_run_success`

## Strengths
- Clear pipeline
- Policy is enforced before execution
- Unknown tool is handled explicitly
- Readable orchestration logic

## Issues Detected
- Planner output contract is implicit and not validated
- No exception handling around planner, policy, or tool execution
- `dry_run` is not structurally guaranteed by the runtime
- Global singleton-style initialization at module import time
- Runtime is coupled to concrete tools and bootstrap logic
- Tool results are converted to `str`, losing structure
- No payload validation per tool
- Error responses are too generic

## Risk Level
High

## Recommended Improvements
- Introduce explicit execution plan schema
- Add controlled error handling per pipeline stage
- Enforce `dry_run` structurally
- Inject planner, policy engine, and registry
- Move tool registration to bootstrap layer
- Return structured tool output
- Add payload validation contracts
- Improve traceability and domain error modeling