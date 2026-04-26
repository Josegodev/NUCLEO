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

## Components in Current Operation

### API

- FastAPI application
- `POST /agent/run`
- `POST /agent/run` accepts optional `X-Idempotency-Key`
- `GET /tools`
- `GET /`

### AgentService

- Thin facade over runtime
- Delegates execution with request and execution context

### Runtime

- Coordinates planner, policy, registry, tool execution
- Evaluates policy before resolving the executable tool instance
- Validates planner output before policy, registry, or tool execution
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
- Allows `disk_info`
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

### LLM Lab / Experimental Side Path

`runtime_lab/llm_lab/` exists inside the repository, but it is a lateral
experimental observation path. It is not part of the production runtime.

Purpose:

- load NUCLEO context for external/local model questions
- run local Mistral/Qwen chats through Ollama
- keep local chat memory in SQLite files under `runtime_lab/llm_lab/`
- generate HARDENING review reports under `runtime_lab/llm_lab/reports/`

Current integration with runtime:

- none
- no calls to `AgentService`
- no calls to `AgentRuntime`
- no interaction with `Planner`, `PolicyEngine`, `ToolRegistry`, or production
  `Tools`

Permissions:

- read repository context
- write lab-only reports and lab-only SQLite memory
- observe and summarize

Forbidden actions:

- execute production tools
- modify policy
- call `/agent/run` automatically
- act as Planner
- register tools in the production `ToolRegistry`

Related context-export script:

- `scripts/export_nucleo_context.py` reads `README.md`,
  `docs/architecture.md`, `docs/operations/operational_state.md`,
  `docs/operations/session_log.md`, and `docs/modules/*.md`
- it writes `llm_context/nucleo_context_snapshot.md` and
  `llm_context/nucleo_context_snapshot.json`
- it must not import or call `AgentService`, `AgentRuntime`, `Planner`,
  `PolicyEngine`, `ToolRegistry`, or `Tools`

## Verified Technical Characteristics

- `ExecutionContext` is currently part of the runtime pipeline
- `AgentResponse` currently exposes structured `result`
- Production tool registration happens in the production tool registry
- Planner output is typed as `PlannedAction`
- `dry_run` is structurally enforced: tools are not executed
- Production policy does not deeply evaluate payload
- Experimental generated tools are not auto-registered in production
- Mistral/Qwen are not part of the production execution flow
- `POST /agent/run` idempotency is handled at the API boundary, before
  `AgentService` delegates into `AgentRuntime`

## `/agent/run` Idempotency Contract

- Without `X-Idempotency-Key`, `/agent/run` keeps the existing behavior and
  delegates every request to `AgentService`.
- With a non-empty `X-Idempotency-Key` of at most 128 characters, the first
  request stores the returned `AgentResponse` in process memory.
- A retry using the same authenticated principal and same idempotency key returns
  the cached `AgentResponse` without calling `AgentRuntime` again.
- The cache is local to the current Python process. It is not Redis-backed, not
  shared across workers, and is reset on process restart.
- Idempotency is not implemented inside `AgentRuntime`, `Planner`,
  `PolicyEngine`, `ToolRegistry`, or tools.

## Operational Constraints

- Single-machine local execution is the current explicit operating model
- Production and lab paths coexist in the codebase but must remain separated
- Experimental generation services exist as isolated code and are not connected
  to the stable `/agent/run` flow
- Runtime simplicity is still prioritized over aggressive expansion

## Open Issues

- No complete payload validation per tool
- No full structured runtime error taxonomy
- Runtime trace is in-memory only and not exposed through API
- No production promotion workflow for lab-generated tools
- Mixing `llm_lab` outputs with runtime decisions would break the current
  deterministic boundary

## Working Rules

- Keep production runtime stable first
- Treat `docs/architecture.md` as source of truth for verified behavior
- Treat `docs/vision/architecture_vision.md` as future-only
- Treat experimental lab as isolated and non-production by default
