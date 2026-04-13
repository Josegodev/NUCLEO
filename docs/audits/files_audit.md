## app/main.py

### Purpose
Application entrypoint for the FastAPI server.

### Current responsibility
- Create FastAPI app
- Register API routers
- Expose HTTP interface

### What it should not do
- Agent execution logic
- Planning logic
- Policy logic
- Tool execution
- Business rules

### Current maturity
Simple and correct

---

## app/api/routes/agent.py

### Purpose
HTTP entrypoint for agent execution.

### Current responsibility
- Receive POST /agent/run requests
- Validate input via AgentRequest
- Call AgentService
- Return AgentResponse

### What it should not do
- Planning logic
- Policy logic
- Tool execution logic
- Business rules

### Current maturity
Simple and correct

### Risks
- Service instantiated without dependency injection
- No request-level tracing or logging

### Future evolution
- Dependency injection for AgentService
- Logging and tracing
- Authentication layer

---

## app/runtime/orchestrator.py

### Purpose
Central execution coordinator of the agent runtime.

### Current responsibility
- Receive AgentRequest
- Ask planner for tool + payload
- Ask PolicyEngine whether execution is allowed
- Resolve tool via ToolRegistry
- Execute tool
- Return AgentResponse

### What it should not do
- HTTP handling
- Tool implementation logic
- Planner logic
- Deep business rules

### Current maturity
Functional and well-oriented, but structurally incomplete

### Strengths
- Clear execution flow
- Separation between planning, policy, and tool execution
- Explicit policy gate before execution
- Handles unknown tools explicitly

### Critical limitations
- Planner contract is implicit (dict with `tool` and `payload`)
- No validation of planner output
- No validation of payload per tool
- Tool results are stringified, losing structure
- No exception handling:
  - planner failures propagate
  - policy failures propagate
  - tool execution failures propagate
- `dry_run` is not enforced:
  - policy ignores it
  - runtime still executes tools
- Global dependencies (planner, registry, policy engine) initialized at import time

### Risks
- Fragile execution pipeline under unexpected inputs
- No guaranteed response contract under failure
- Unsafe behavior if non-read-only tools are introduced
- Tight coupling to global runtime configuration

### Future evolution
- Add controlled error handling per stage
- Return structured tool output
- Enforce `dry_run`
- Introduce dependency injection
- Add minimal execution tracing
- Introduce ExecutionContext (later)

---

# Files Audit

## app/main.py
- FastAPI entrypoint
- Registers routers

## app/api/routes/agent.py
- HTTP interface for agent
- Calls AgentService (not runtime directly)

## app/runtime/orchestrator.py
- Coordinates execution flow
- Planner → Policy → Registry → Tool → Response

## app/runtime/planner.py
- Rule-based planner using substring matching
- Returns implicit execution plan (dict)

## app/policies/engine.py
- Static whitelist policy (tool-name based)
- Ignores payload and dry_run

## app/tools/registry.py
- Dictionary-based tool registry
- No duplicate protection
- Resolves tools by name

## app/tools/base.py
- Defines tool interface
- Not enforced (no abstract base class)
- Metadata not validated

## Summary

The system is modular and correctly separated, but relies heavily on implicit contracts:

- planner → runtime contract is not validated
- tool input/output is not structured
- policy does not enforce execution modes
- runtime does not handle failures

The architecture is sound, but the implementation is still in a **bootstrap stage** and requires contract reinforcement before scaling.

TEST_SAVE_ARCHITECTURE_130426