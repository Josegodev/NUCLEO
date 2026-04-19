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
- `ExecutionContext` propagated across API, runtime, policy, and tools
- `AgentResponse` with `status`, `message`, and optional `result`

## Current Experimental State

The repository also contains an isolated experimental lab subsystem:

- capability-gap signal from planner when explicitly requested
- deterministic proposal generation placeholder
- isolated staging registry
- lab-only skeleton generation
- audit artifact generation

This subsystem is implemented but not part of the stable production registry path.

## Main Remaining Weaknesses

### 1. Weak internal contracts

- planner output is still implicit
- tool payload contracts are still implicit
- tool output is not yet standardized beyond current response container

### 2. Incomplete execution control

- `dry_run` is still not structurally enforced for production execution
- policy does not evaluate payload deeply
- `read_only` and `risk_level` metadata are still not policy-enforced

### 3. Runtime robustness gaps

- limited structured exception handling in runtime
- no formal domain error taxonomy

### 4. Bootstrap coupling

- planner, policy engine, registry, and experimental services are still composed at module import time

### 5. Documentation and operational drift risk

- historical documents contain earlier snapshots that must be read as logs, not current truth
- `docs_esp/` is a maintained translation of `docs/`, but not the primary verified source

## Evolution Priorities

### Priority 1 - Reinforce contracts

- introduce typed execution plan
- define structured tool payload contracts
- define stronger tool result contracts
- strengthen `BaseTool` contract

### Priority 2 - Enforce execution control

- make `dry_run` meaningful
- use tool metadata in policy decisions
- prepare payload-aware policy checks

### Priority 3 - Improve runtime robustness

- add controlled error handling by pipeline stage
- standardize domain error responses
- improve traceability

### Priority 4 - Decouple composition from orchestration

- inject planner, registry, and policy into runtime
- move production and lab composition into dedicated bootstrap layer

### Priority 5 - Mature experimental lab

- real review workflow for staging registry
- richer artifact metadata
- explicit promotion process
- real LLM integration only behind controlled boundaries

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
