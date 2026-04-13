# Evolution Map

## Purpose

This document maps the transition from the current audited system state
to a more robust and scalable modular agent runtime.

It is based on verified code behavior, not intended architecture alone.

---

## Current State (audited)

The system currently provides:

- FastAPI entrypoint for agent execution
- AgentService as thin façade over runtime
- AgentRuntime as central execution orchestrator
- Rule-based Planner
- Static whitelist-based PolicyEngine
- ToolRegistry for tool lookup
- BaseTool as weak common interface
- Initial tools: `echo`, `system_info`

### Current characteristics

- execution flow is clear and modular
- contracts between components are mostly implicit
- planner returns a plain dict (`tool`, `payload`)
- policy evaluates only tool name
- `dry_run` exists but is not structurally enforced
- tool outputs are stringified into `AgentResponse.message`
- runtime does not catch planner / policy / tool exceptions
- tool registration happens at module import time

---

## Main Weaknesses

### 1. Weak internal contracts
- planner output is not typed or validated
- tool payload contracts are implicit
- tool output format is not standardized

### 2. Incomplete execution safety
- `dry_run` is not guaranteed by design
- policy does not evaluate payload or tool metadata
- `read_only` and `risk_level` are declared but not enforced

### 3. Limited error robustness
- no structured exception handling in runtime
- failures can propagate outside the domain response model

### 4. Tight bootstrap coupling
- planner, registry and policy engine are created globally
- runtime is coupled to concrete initialization choices

### 5. Limited scalability of decision logic
- planner is based on simple substring matching
- policy is based on hardcoded tool-name allowlist

---

## Evolution Priorities

## Priority 1 — Reinforce contracts

Objective:
Make interfaces explicit and machine-checkable.

Actions:
- introduce typed `ExecutionPlan`
- define structured tool input schemas
- define structured tool output/result model
- strengthen `BaseTool` as real abstract contract

Expected impact:
- fewer hidden assumptions
- safer refactors
- easier testing and extension

---

## Priority 2 — Enforce execution control

Objective:
Make safety guarantees real, especially around execution modes.

Actions:
- enforce meaningful `dry_run`
- use `read_only` and `risk_level` in policy decisions
- prepare payload-aware policy checks

Expected impact:
- stronger execution guarantees
- safer future non-read-only tools

---

## Priority 3 — Improve runtime robustness

Objective:
Make the orchestration layer resilient to failure.

Actions:
- add controlled exception handling per pipeline stage
- standardize error responses
- improve traceability of failures and decisions

Expected impact:
- predictable behavior under failure
- easier debugging and auditability

---

## Priority 4 — Decouple composition from orchestration

Objective:
Separate system wiring from system execution.

Actions:
- inject planner, registry and policy engine into runtime
- move tool registration out of orchestrator module
- prepare bootstrap/composition layer

Expected impact:
- better testability
- cleaner architecture
- easier environment-specific configuration

---

## Priority 5 — Evolve decision and policy layers

Objective:
Prepare the system for growth without losing control.

Actions:
- evolve planner from ad hoc keyword checks to declarative rules
- evolve policy from name allowlist to metadata/capability-based rules
- add minimal execution trace metadata

Expected impact:
- better scalability
- improved observability
- smoother path toward multi-step or LLM-assisted planning

---

## Suggested Evolution Order

1. Contracts
2. Dry-run and policy enforcement
3. Runtime error handling
4. Dependency injection / bootstrap cleanup
5. Planner and policy evolution
6. Advanced capabilities:
   - execution context
   - traceability
   - multi-step planning
   - LLM integration
   - memory/state

---

## Not Yet Recommended

The following should not be prioritized before contracts and control are reinforced:

- multi-step orchestration
- memory/state handling
- LLM-based planner replacement
- autonomous tool composition

Reason:
the current system is modular and understandable, but still relies on fragile implicit assumptions.

---

## Target Direction

A robust modular runtime with:

- explicit contracts
- controlled execution
- typed planning/output structures
- policy-aware tool execution
- clean dependency boundaries
- traceable and testable orchestration

TEST_SAVE_ARCHITECTURE_130426