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
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse

Experimental opt-in branch:

AgentRequest with `experimental_tool_generation=True`  
→ Planner may emit `capability_gap_detected`  
→ AgentRuntime handles proposal / staging / skeleton generation  
→ returns controlled `capability_gap` response  
→ production registry unchanged

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
- Contains current experimental capability-gap handling path

### Planner

- Rule-based
- Returns implicit dict contracts
- Can emit experimental gap signal only when request explicitly opts in

### PolicyEngine

- Deny-by-default on production tool names
- Allows `echo`
- Allows `system_info` only for admin context

### Production Tools

- `echo`
- `system_info`

### Experimental Lab

- Proposal generation service
- Tool skeleton generation service
- Staging registry
- Audit store
- All isolated under `runtime_lab/`

## Verified Technical Characteristics

- `ExecutionContext` is currently part of the runtime pipeline
- `AgentResponse` currently exposes structured `result`
- Production tool registration happens at module import time in runtime orchestrator
- Planner output remains implicit
- `dry_run` is still not structurally enforced for production execution
- Production policy does not deeply evaluate payload
- Experimental generated tools are not auto-registered in production

## Operational Constraints

- Single-machine local execution is the current explicit operating model
- Production and lab paths coexist in the codebase but must remain separated
- Experimental generation is request-gated, not ambient behavior
- Runtime simplicity is still prioritized over aggressive expansion

## Open Issues

- No explicit typed execution plan
- No complete payload validation per tool
- No full structured runtime error taxonomy
- No integrated production audit trail
- No production promotion workflow for lab-generated tools
- `dry_run` semantics still incomplete

## Working Rules

- Keep production runtime stable first
- Treat `docs/architecture.md` as source of truth for verified behavior
- Treat `docs/vision/architecture_vision.md` as future-only
- Treat experimental lab as isolated and non-production by default
