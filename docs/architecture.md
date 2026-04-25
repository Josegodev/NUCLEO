# Architecture - Verified Current State

## Purpose

This document is the source of truth for architecture that can be verified directly in the current codebase. It describes implemented behavior, explicit experimental behavior, and known limitations when they are observable in code.

## Documentation Convention

This repository separates documentation into layers:

- Verified architecture: implemented and code-verifiable behavior
- Target architecture / vision: intended future design
- Operations: run state, execution rules, and historical logs
- Audits: critical evaluation, risks, gaps, and consistency checks
- Session logs: chronological record of decisions and changes

If a capability is experimental, partial, or future, it must be labeled explicitly.

## Verified Execution Flow

Stable runtime flow:

AgentRequest  
→ AgentService  
→ AgentRuntime  
→ Planner  
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse

The runtime also records an internal in-memory execution trace for each
execution. This trace is not part of the public API response contract.

## Verified Endpoints

- `GET /` -> health response
- `GET /tools` -> list registered production tools
- `POST /agent/run` -> execute agent runtime

## Verified Component Responsibilities

### API

- Receives HTTP requests
- Resolves authentication at request boundary
- Builds `ExecutionContext`
- Delegates to `AgentService`

### AgentService

- Thin service facade over `AgentRuntime`
- Propagates `AgentRequest` and `ExecutionContext`
- Does not own planning, policy, or tool execution

### AgentRuntime

- Coordinates the runtime pipeline
- Calls planner
- Calls policy engine
- Resolves tools through production registry
- Executes production tools
- Records internal planner, policy, and tool steps through the runtime tracer
- Returns `AgentResponse`

### Planner

- Performs simple rule-based planning
- Returns an implicit `dict`
- Can emit either:
  - a production tool plan
  - an experimental `capability_gap_detected` signal when explicitly requested

### PolicyEngine

- Requires authenticated execution context
- Allows `echo`
- Allows `system_info` only for `admin`
- Denies all other production tools by name

### ToolRegistry

- Stores production tool instances in a dictionary
- Resolves tools by `tool.name`
- Is separate from staging and experimental registries

### Production Tools

Currently registered at import time in the production runtime:

- `echo`
- `system_info`
- `disk_info`

### AgentResponse

Current runtime response model contains:

- `status`
- `message`
- `result` optional

`message` is still populated with `str(result)` for backward compatibility.

## Verified Current Contracts

### AgentRequest

Current fields:

- `user_input: str`
- `dry_run: bool = True`
- `experimental_tool_generation: bool = False`

### Planner Output

The planner still returns an implicit `dict`. The contract is not yet strongly typed in the stable runtime.

Observed keys:

- `tool`
- `payload`
- `mode`

When experimental gap detection is triggered, additional keys may appear:

- `original_input`
- `capability_gap`

### PolicyDecision

Current fields:

- `decision`
- `reason`

### Runtime Trace

Internal-only tracing is implemented in `app/runtime/tracing.py`.

`ExecutionTrace` contains:

- `trace_id`
- `request_id`
- `steps`

Each `ExecutionStep` contains:

- `step_id`
- `phase` (`planner`, `policy`, `registry`, or `tool`)
- `input`
- `output`
- `status` (`success`, `denied`, `error`, or `skipped`)
- `error`
- `timestamp`

The first implementation is `InMemoryTracer`. It has no disk persistence and no
external integration.

## Verified Experimental Subsystem

An experimental subsystem for controlled tool proposal and skeleton generation is implemented in isolated modules and `runtime_lab/`.

### Experimental flow

This path is opt-in and does not change the production registry:

AgentRequest with `experimental_tool_generation=True`  
→ Planner may emit `capability_gap_detected`  
→ AgentRuntime handles the gap  
→ ToolProposalService creates a structured proposal  
→ StagingRegistry stores isolated staging state  
→ ToolGenerationService creates a lab-only skeleton  
→ AuditStore records lab events  
→ AgentResponse returns a controlled capability-gap result

### Important architectural rule

Experimental generated tools are not auto-registered in the production `ToolRegistry`.

## Verified Constraints and Limitations

- Planner output is still implicit and not runtime-validated
- `dry_run` is structurally enforced by the runtime: policy is evaluated, the
  tool step is traced, and the production tool is not executed
- Policy is still largely name-based
- Tool metadata such as `read_only` and `risk_level` are not yet enforced by policy
- Production bootstrap still happens at module import time in `orchestrator.py`
- Error handling in runtime is still limited

## Explicitly Not Verified

The following must not be described as implemented production behavior:

- Real LLM-backed planning
- Auto-extension of production registry
- Dynamic package installation
- Arbitrary shell execution
- Autonomous promotion from staging to production

Those behaviors are either not implemented or only documented as future direction elsewhere.
