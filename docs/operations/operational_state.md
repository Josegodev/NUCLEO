# Operational State – NUCLEO

## Purpose

Describe the current operational state of the system,
including verified behavior, constraints, and working rules.

---

## Current Objective

Build a minimal, controlled agent runtime in FastAPI capable of:

- receiving a request
- mapping it to a tool via a planner
- validating execution via a policy layer
- executing the tool
- returning a response

Goal:
Control and clarity over complexity.

---

## Current Architecture (verified)

Execution flow:

AgentRequest  
→ AgentService  
→ AgentRuntime  
→ Planner  
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse  

---

## Components

### API
- FastAPI application
- Endpoint: `/agent/run`
- Health endpoint available

### AgentService
- Thin façade over runtime
- Delegates execution

### Runtime (orchestrator)
- Coordinates execution flow:
  Planner → Policy → Registry → Tool

### Planner
- Rule-based substring matching
- Returns implicit dict: `{tool, payload}`

### Tool Registry
- Dictionary-based registry
- Resolves tools by name

### Tools implemented
- echo
- system_info

### Policy Engine
- Static whitelist:
  - allows: echo, system_info
  - denies all others
- Ignores payload and dry_run

### Schemas
- AgentRequest (user_input, dry_run)
- AgentResponse (status, message)

---

## Verified Technical Characteristics

- Planner output is not validated (implicit contract)
- Policy does not enforce execution mode (`dry_run`)
- Runtime executes tools even in dry_run
- Tool results are stringified (`str(result)`)
- Runtime does not catch exceptions (planner, policy, tool)
- Tool input/output contracts are implicit

---

## Last Stable Point

Commit:
3622055 (HEAD -> main, origin/main)

State:
- /agent/run works
- echo tool works
- system_info tool works
- planner → policy → execution pipeline functional
- response is simple (status + message)

---

## Work Completed

- FastAPI base initialized
- AgentService implemented
- AgentRuntime implemented
- Planner integrated
- ToolRegistry implemented
- echo tool working
- system_info tool working
- Policy layer introduced
- End-to-end execution working

---

## Open Issues (validated)

- No structured execution plan
- No payload validation
- No structured tool output
- No execution trace
- No error handling in runtime
- `dry_run` not enforced
- Policy not using tool metadata

---

## Next Step (STRICT)

Rebuild incrementally, NOT full refactor.

### Immediate action

Add minimal logging inside orchestrator:

- log request_id
- log selected tool
- log policy decision
- log execution result

### Do NOT

- introduce ExecutionContext yet
- refactor response structure
- modify tools deeply

---

## Constraints

- Single-machine execution (local)
- Must remain understandable
- Changes must be incremental
- Each change testable via `/agent/run`

---

## Working Rules

- One change = one commit
- No large refactors
- Always test via `/agent/run`
- Update SESSION_LOG.md after each session
- Update development_plan.md before stopping

