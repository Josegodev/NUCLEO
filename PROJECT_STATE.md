# Project State

## Current objective
Build a minimal, controlled agent runtime in FastAPI capable of:
- receiving a request
- mapping it to a tool via a planner
- validating execution via a policy layer
- executing the tool
- returning a structured response

Goal is NOT complexity, but control and clarity.

---

## Current architecture

### API
- FastAPI application
- Endpoint: `/agent/run`
- Health endpoint available

### Runtime (orchestrator)
- Receives AgentRequest
- Calls Planner
- Resolves tool via ToolRegistry
- Applies PolicyEngine
- Executes tool
- Returns AgentResponse

### Planner
- Simple mapping: user_input → tool + payload
- Likely rule-based (no LLM)

### Tool Registry
- Registers available tools
- Resolves tool by name

### Tools implemented
- echo
- system_info

### Policy Engine
- Basic allow/deny logic
- Currently permissive (mostly allow)

### Schemas
- AgentRequest (user_input, dry_run)
- AgentResponse (status, message)
- No execution context yet (or minimal)

---

## Last stable point

Commit:
3622055 (HEAD -> main, origin/main)

State:
- /agent/run works
- echo tool works
- system_info tool works
- policy engine integrated
- planner-tool execution pipeline functional
- response is simple (status + message)

---

## Work completed

- FastAPI base initialized
- Agent runtime (orchestrator) implemented
- Planner integrated
- Tool registry implemented
- echo tool working
- system_info tool working
- Policy layer introduced
- End-to-end execution working

---

## What was attempted (and rolled back)

- Full execution context (ExecutionContext, ToolCallRecord)
- Tool metadata system
- Structured response with result + execution
- Refactor of orchestrator to support tracing

Reason for rollback:
- Too large refactor in a single session
- Loss of control and traceability
- Hard to maintain across sessions

---

## Open issues

- No persistent memory between sessions
- No execution trace (tool_calls, durations, etc.)
- Policy engine not using risk levels yet
- Planner is simplistic (string matching)
- No structured response payload

---

## Next step (STRICT)

Rebuild incrementally, NOT full refactor.

Next action:

1. Add minimal logging inside orchestrator:
   - log request_id
   - log selected tool
   - log policy decision
   - log execution result

DO NOT:
- introduce ExecutionContext yet
- refactor response structure
- modify tools deeply

---

## Files involved

Core files:

- app/main.py
- app/runtime/orchestrator.py
- app/runtime/planner.py
- app/tools/registry.py
- app/tools/implementations/echo_tool.py
- app/tools/implementations/system_info_tool.py
- app/policies/engine.py
- app/schemas/requests.py
- app/schemas/responses.py

---

## Decisions

- Keep architecture modular but simple
- Avoid overengineering
- No async complexity for now
- No database
- No LLM dependency in core runtime
- Prefer explicit control over automation

---

## Constraints

- Single-machine execution (local)
- Must remain understandable without external tools
- Changes must be incremental
- Each change must be testable via /agent/run

---

## Working rules

- One change = one commit
- No large refactors in one session
- Always test via /agent/run before continuing
- Update SESSION_LOG.md after each session
- Update NEXT_STEPS.md before stopping
