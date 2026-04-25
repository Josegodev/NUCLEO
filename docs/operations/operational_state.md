# Operational State - NUCLEO

## Purpose

Describe the current operational state of the system using only behavior that is verified in code or directly implied by repository structure.

## Current Objective

Operate a minimal, controlled modular agent runtime on FastAPI while keeping the production execution path understandable and isolated from experimental lab capabilities.

## Current Verified Architecture

Production flow:

AgentRequest  
→ AgentService  
→ AgentRuntime  
→ Planner  
→ ToolRegistry  
→ PolicyEngine  
→ Tool  
→ AgentResponse

## Components in Current Operation

### API

- FastAPI application
- `POST /agent/run`
- `GET /tools`
- `GET /`

### AgentService

- Thin facade over runtime
- Delegates execution with request and execution context

### Runtime

- Coordinates planner, policy, registry, tool execution
- Validates planner output before registry, policy, or tool execution
- Returns `no_plan` without executing tools when planner has no deterministic match

### Planner

- Rule-based
- Uses a small explicit table of deterministic rules
- Returns typed `PlannedAction`
- Emits `planned` or `no_plan`
- Does not authorize or execute tools

### PolicyEngine

- Deny-by-default on production tool names
- Allows `echo`
- Allows `system_info` only for admin context

### Production Tools

- `echo`
- `system_info`
- `disk_info`

### Experimental Lab

- Proposal generation service
- Tool skeleton generation service
- Staging registry
- Audit store
- All isolated under `runtime_lab/`

## Verified Technical Characteristics

- `ExecutionContext` is currently part of the runtime pipeline
- `AgentResponse` currently exposes structured `result`
- Production tool registration happens in the production tool registry
- Planner output is typed as `PlannedAction`
- `dry_run` is structurally enforced: tools are not executed
- Production policy does not deeply evaluate payload
- Experimental generated tools are not auto-registered in production

## Operational Constraints

- Single-machine local execution is the current explicit operating model
- Production and lab paths coexist in the codebase but must remain separated
- Experimental generation is request-gated, not ambient behavior
- Runtime simplicity is still prioritized over aggressive expansion

## Open Issues

- No complete payload validation per tool
- No full structured runtime error taxonomy
- Runtime trace is in-memory only and not exposed through API
- No production promotion workflow for lab-generated tools

## Working Rules

- Keep production runtime stable first
- Treat `docs/architecture.md` as source of truth for verified behavior
- Treat `docs/vision/architecture_vision.md` as future-only
- Treat experimental lab as isolated and non-production by default
