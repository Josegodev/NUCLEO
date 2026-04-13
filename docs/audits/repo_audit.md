# Repo Audit

## Purpose

This document evaluates the repository as a codebase structure:
- directory organization
- module boundaries
- naming consistency
- scalability risks in project layout
- alignment between physical structure and intended architecture

It is based on the current audited implementation.

---

## Current Repository Structure

Current high-level structure (audited):

## Repository Structure (real)

```text
app/
  -main.py                    → FastAPI entrypoint; initializes app and registers routes

  api/
    routes/
      agent.py              → POST `/agent/run`; ejecuta el agente vía AgentService
      health.py             → GET `/health`; endpoint de estado (liveness)
      tools.py              → GET `/tools`; expone tools registradas

  -services/
    agent_service.py        → Thin façade; delegates execution to AgentRuntime

  -runtime/
    orchestrator.py         → Core execution pipeline; coordinates planner, policy and tools
    planner.py              → Rule-based decision logic; maps user_input → tool + payload
    dispatcher.py           → (planned) execution router; intended to decide where/how tools run

  -policies/
    engine.py               → Execution control; allow/deny based on tool name
    models.py               → PolicyDecision schema (decision + reason)

  -tools/
    base.py                 → Tool interface definition (BaseTool)
    registry.py             → Tool registry; resolves tools by name
    local/                  → Concrete tool implementations (e.g., echo, system_info)

  -schemas/
    requests.py             → AgentRequest model (input contract)
    responses.py            → AgentResponse model (output contract)
    execution.py            → Execution models (PlanStep, ToolResult)

docs/
  -architecture.md           → Verified system behavior (source of truth)
  -evolution_map.md          → Technical roadmap and evolution priorities

  -modules/                  → Per-module audit documentation (runtime, planner, etc.)
  -audits/                   → Repository and file-level audits
  -operations/               → Operational state, session log, snapshots
  -planning/                 → Development plan and next steps
  -vision/                   → Target architecture (future design)

### Structural assessment

The repository is currently small, readable, and easy to navigate.

The layout already reflects the main architectural boundaries:
- API layer
- runtime/orchestration
- policy layer
- tools layer
- schemas
- documentation

This is a good foundation for controlled growth.

---

## Strengths

- Clear top-level separation by responsibility
- Runtime logic is not mixed into API entrypoints
- Tools are isolated from orchestration logic
- Schemas are separated from execution components
- Documentation directory already exists

---

## Current Weaknesses

### 1. Bootstrap wiring is still embedded in runtime module
Tool registration and core component instantiation currently happen inside the orchestrator module.

Impact:
- hidden initialization
- tighter coupling
- harder testing and configuration

### 2. Repository structure does not yet distinguish composition from execution
There is no dedicated bootstrap/container/composition layer.

Impact:
- runtime module takes on setup responsibilities
- dependency injection path is not yet prepared


### 3. No dedicated tests structure observed in audited scope
A test layout has not yet been established in the reviewed material.

Impact:
- difficult regression protection as contracts evolve

---

## Naming Assessment

### Positive points
- Names are generally explicit and readable
- `runtime`, `policies`, `tools`, `schemas` are coherent package names
- `orchestrator.py` correctly signals central execution role

### Watch points
- `AgentService` vs `AgentRuntime` must remain clearly differentiated
- “runtime”, “orchestrator”, and “service” should not blur over time
- tool names used across planner / policy / registry remain string-coupled

---

## Scalability Assessment

The repository is suitable for the current bootstrap phase.

It can scale correctly if the next structural changes are controlled:

1. reinforce contracts
2. separate bootstrap/composition from runtime
3. add tests
4. keep documentation synced with verified behavior

Without these changes, growth will likely increase coupling faster than capability.

---

## Recommended Next Structural Additions

### Short term
- `tests/`
- `docs/modules/`
- optional `app/bootstrap/` or `app/container/`

### Medium term
- `app/runtime/models.py` or equivalent for execution plan / runtime contracts
- tool-specific payload schemas
- structured error models

---

## Overall Assessment

Repository structure is currently:

- simple
- coherent
- easy to navigate
- appropriate for an early modular runtime

Main risk is not repository chaos, but architectural drift caused by:
- implicit contracts
- hidden bootstrap coupling
- insufficient test scaffolding

The repo foundation is good enough to continue, provided that contracts and composition boundaries are reinforced before major feature growth.

