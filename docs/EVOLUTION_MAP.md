# Evolution Map

## Purpose

This document maps the transition from the currently verified system state to a more robust runtime, while distinguishing clearly between implemented, partial, experimental, and future capabilities.

## Current Verified State

The repository currently provides:

- FastAPI entrypoint for runtime execution
- `AgentService` as facade over `AgentRuntime`
- `AgentRuntime` as production orchestrator
- Rule-based `Planner`
- Name-based `PolicyEngine` with role check for `system_info`
- `ToolRegistry` for production tool lookup
- Production tools:
  - `echo`
  - `system_info`
  - `disk_info`
- `ExecutionContext` propagated across API, runtime, policy, and tools
- Explicit artifact contracts for planned actions, policy decisions, tool
  contracts, and execution results
- `AgentResponse` with closed `status`, optional structured `result`,
  structured `errors`, `trace_id`, and `version`

## Current Experimental State

The repository also contains an isolated experimental lab subsystem:

- deterministic proposal generation placeholder
- isolated staging registry
- lab-only skeleton generation
- audit artifact generation
- `runtime_lab/llm_lab/` as a lateral local observation path for Mistral/Qwen
  chats and HARDENING reports

This subsystem is implemented but not part of the stable production registry path.
Mistral/Qwen are not part of AgentService, Runtime, Planner, PolicyEngine,
ToolRegistry, or Tools.

## Main Remaining Weaknesses

### 1. Weak internal contracts

- planner output is typed and versioned as `PlannedAction`
- tool payload and output contracts are explicit for registered production tools
- `ToolContractArtifact` is mandatory at production registration time

### 2. Incomplete execution control

- `dry_run=True` validates planning, policy, registry, and tracing, but does
  not call `tool.run(...)`
- policy validates payload shape against the selected tool contract
- `read_only` and `risk_level` metadata are still not policy-enforced

### 3. Runtime robustness gaps

- runtime now returns structured execution-result artifacts
- further domain-specific error taxonomy may still be refined

### 4. Bootstrap coupling

- planner, policy engine, and registry are still composed at module import time

### 5. Documentation and operational drift risk

- historical documents contain earlier snapshots that must be read as logs, not current truth
- `docs_esp/` is a maintained translation of `docs/`, but not the primary verified source

## Evolution Priorities

### Priority 1 - Reinforce contracts

- keep artifact contracts small and explicit
- preserve strict enum-backed policy decisions
- keep tool input/output schemas aligned with registered tool contracts
- avoid adding new abstractions unless a contract gap requires it

### Priority 2 - Enforce execution control

- keep `dry_run` deterministic, non-executing, and covered by tests
- use tool metadata in policy decisions
- prepare payload-aware policy checks

### Priority 3 - Improve runtime robustness

- keep controlled error handling by pipeline stage covered by tests
- refine domain error codes only when concrete runtime ambiguity appears
- improve traceability

### Priority 4 - Decouple composition from orchestration

- inject planner, registry, and policy into runtime
- move production and lab composition into dedicated bootstrap layer

### Priority 5 - Mature experimental lab

- real review workflow for staging registry
- richer artifact metadata
- explicit promotion process
- real LLM integration only behind controlled boundaries
- keep `llm_lab` as observation-only unless a future explicit design changes
  that boundary

## Not Yet Recommended

The following should still not be treated as production priorities before contracts and execution control are stronger:

- autonomous tool activation
- production self-extension
- uncontrolled LLM planner authority
- distributed execution
- implicit memory/state orchestration

## Target Outcome

A runtime with:

- explicit contracts
- controlled execution
- stable production registry
- isolated experimental lab
- traceable orchestration
- documentation that clearly separates current state from future vision
