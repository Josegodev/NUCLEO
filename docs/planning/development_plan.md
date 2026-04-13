# Development Plan – NUCLEO

## Purpose

Define the next technical steps after completing the full system audit.

The system is now understood.  
The next phase is to reinforce contracts, control, and robustness before adding new features.

---

## Current Status

Audit completed for:

- AgentService
- AgentRuntime (orchestrator)
- Planner
- PolicyEngine
- ToolRegistry
- BaseTool

Documentation created:

- architecture.md (verified behavior)
- evolution_map.md
- modules audit
- repo audit

---

## Phase 1 — Contract Reinforcement (HIGH PRIORITY)

Objective:
Eliminate implicit contracts and make system behavior explicit.

Actions:

- Introduce `ExecutionPlan` (replace dict in planner)
- Define structured tool output (avoid `str(result)`)
- Define payload schemas per tool
- Strengthen BaseTool as abstract interface

---

## Phase 2 — Execution Control (HIGH PRIORITY)

Objective:
Ensure safe and predictable execution.

Actions:

- Enforce `dry_run` at runtime or policy level
- Use `read_only` and `risk_level` in policy decisions
- Prevent execution of unsafe tools in dry_run

---

## Phase 3 — Error Handling (HIGH PRIORITY)

Objective:
Guarantee controlled system behavior under failure.

Actions:

- Add try/catch per pipeline stage:
  - planner
  - policy
  - tool execution
- Standardize error responses
- Ensure runtime always returns AgentResponse

---

## Phase 4 — Dependency Decoupling (MEDIUM PRIORITY)

Objective:
Remove hidden coupling and improve testability.

Actions:

- Inject planner, policy engine, and registry into runtime
- Move tool registration out of orchestrator module
- Prepare bootstrap/composition layer

---

## Phase 5 — Minimal Observability (MEDIUM PRIORITY)

Objective:
Make system behavior traceable.

Actions:

- Log:
  - selected tool
  - policy decision
  - execution result
- Prepare ExecutionContext (later)

---

## Phase 6 — Persistence (DATABASE) (MEDIUM PRIORITY)

Objective:
Introduce persistence to store system state, executions, and traceability.

Context:
The system is currently fully stateless.  
There is no storage for executions, results, or context.

Initial scope (minimal, no overengineering):

- Record runtime executions:
  - request_id
  - user_input
  - selected tool
  - policy decision
  - result
  - timestamp

- Persist structured logs (as an alternative or complement to plain logging)

Technical decisions to define:

- Database type:
  - SQLite (local, simple, recommended to start)
  - PostgreSQL (if scaling to multi-environment)

- Minimal data model:
  - ExecutionRecord
  - (optional) ToolExecution
  - (optional) PolicyDecisionLog

- Integration strategy:
  - DO NOT couple directly to the runtime core
  - introduce a future layer (`storage/` or `persistence/`)
  - use a simple interface (lightweight repository pattern)

Constraints:

- Do not introduce a complex ORM at this stage
- Do not break runtime simplicity
- Persistence must be optional (feature toggle possible)

Expected impact:

- Real execution traceability
- Foundation for advanced debugging
- Preparation for auditing and analysis
- Future base for memory/state (without implementing it yet)
---

## Phase 7 — Planner & Policy Evolution (LOW PRIORITY)

Only after previous phases are complete.

Actions:

- Improve planner logic (rules → structured matching)
- Move policy from tool-name allowlist to metadata-based rules

---

## Not Allowed Yet

Do NOT introduce:

- LLM-based planner
- multi-step execution
- memory/state
- distributed execution

Reason:
The system still relies on fragile implicit contracts.

---

## Guiding Principle

Stabilize before expanding.

The current system is modular and correct in structure,  
but must become robust before increasing complexity.