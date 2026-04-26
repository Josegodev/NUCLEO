# Session Log

## 2026-04-10

- Implemented runtime orchestration.
- Added `echo` and `system_info` tools.
- Introduced a first policy layer.
- Attempted execution-context integration.
- Rolled back the first context attempt due to excessive refactor scope.

## 2026-04-11

- Audited:
  - `main.py`
  - `api/routes/agent.py`
  - `runtime/orchestrator.py`
- Clarified runtime structure:
  - API → AgentService → Runtime → Planner → Policy → Registry → Tool → Response
- Identified limitations:
  - no execution tracing
  - global dependencies in runtime
  - simple planner
  - basic policy engine
  - response not structured

## 2026-04-12

- Continued system audit over:
  - planner
  - policy engine
  - tool registry
  - base tool
  - tool implementations
- Verified planner → policy → registry → tool flow.
- Restructured tools toward `tools/local/`.
- Added reserved or preparatory directories:
  - `clients/`
  - `audit/`
  - `runtime/dispatcher.py`
- Introduced `AgentService` as a separate service layer.

## 2026-04-13

- Completed technical audit of:
  - AgentService
  - AgentRuntime
  - Planner
  - PolicyEngine
  - ToolRegistry
  - BaseTool
- Identified critical gaps:
  - implicit contracts
  - no enforced dry-run
  - limited runtime error handling
  - unstructured tool output
  - name-based policy
- Reorganized documentation into:
  - architecture
  - vision
  - planning
  - operations
  - audits

## 2026-04-13 - Authentication and ExecutionContext Integration

- Implemented request-scoped API-key authentication.
- Added `ExecutionContext`.
- Propagated context through:
  - route dependency
  - AgentService
  - AgentRuntime
  - PolicyEngine
  - tools
- Verified role-aware policy behavior for `system_info`.

## 2026-04-18 - Structured Result Preservation

- Modified:
  - `app/schemas/responses.py`
  - `app/runtime/orchestrator.py`
- Preserved structured tool output in `AgentResponse.result`.
- Kept `message=str(result)` for backward compatibility.

## 2026-04-19 - Experimental LLM Tool Expansion Skeleton

- Added isolated experimental modules for:
  - tool proposals
  - tool generation
  - staging registry
  - audit store
- Added `experimental_tool_generation` request flag.
- Added planner capability-gap signaling.
- Added controlled runtime branch for:
  - proposal creation
  - staging registration
  - skeleton generation
  - audit artifact generation
- Kept production tool registry unchanged.
- Real LLM integration remains unimplemented.

## 2026-04-19 - Documentation Normalization

- Audited Markdown documentation across the repository.
- Defined documentation layers:
  - verified architecture
  - target vision
  - operations
  - audits
  - session logs
- Normalized primary docs under `docs/`.
- Marked `docs_esp/` as translation mirror rather than primary verified source.
- Added:
  - `docs/audits/documentation_consistency_audit.md`
  - `docs/operations/session_log_docs_normalization.md`

## 2026-04-19 - `disk_info` Tool Integration

- Implemented:
  - `app/tools/local/disk_info_tool.py`
  - `DiskInfoTool`
  - `name = "disk_info"`
- Confirmed tool contract:
  - read-only tool
  - standard library only
  - uses `shutil.disk_usage`
  - cross-platform default path behavior:
    - Windows → `C:\\`
    - Linux/macOS → `/`
- Corrected semantic naming from `memory_info` to `disk_info`.
- Updated planner behavior to support:
  - explicit `tool` + `payload`
  - `disk_info` resolution from text input
  - optional `path=...` extraction without overriding structured payload
- Updated policy whitelist to allow `disk_info`.
- Resolved runtime failure `Planner requested unknown tool: disk_info`.
- Identified and fixed registry wiring issue:
  - duplicated `ToolRegistry()` instances
  - missing `DiskInfoTool()` registration
  - centralized shared registry instance for runtime and API routes
- Validated end-to-end flow:
  - API → Planner → Policy → Registry → Tool → Response
- Recorded successful real execution result for `path = C:\\`:
  - `total_gb = 236.55`
  - `used_gb = 228.43`
  - `free_gb = 8.11`
  - `free_percent = 3.43`
  - `os = Windows`
- Documented pending improvement:
  - API response remains double-encapsulated
  - `message` contains serialized JSON
  - `result` contains the actual structured payload
- Marked `disk_info` integration as functional.
- Next steps:
  - clean response layer
  - add more local system-observation tools

## 2026-04-23

- Recovered system baseline after rollback
- Identified critical issues:
  - PolicyDecision not closed
  - Policy/Registry drift risk
  - Missing deterministic runner
- Entering HARDENING phase (contracts + determinism)

## 2026-04-25

- Added minimal internal runtime tracing:
  - `ExecutionTrace`
  - `ExecutionStep`
  - `Tracer`
  - `InMemoryTracer`
- Integrated tracing in `AgentRuntime` for:
  - planner result
  - policy decision
  - registry resolution
  - tool execution or dry-run skip
- Kept trace internal and out of the public `AgentResponse` contract.
- Enforced `dry_run=True` as non-executing runtime behavior while still tracing
  the intended tool step as `skipped`.
- Added unittest coverage for allowed, denied, dry-run, unknown-tool, tool-error,
  tracer-failure, and API response-contract behavior.
- Hardened planner contract:
  - added typed `PlannedAction`
  - reduced planner statuses to `planned` and `no_plan`
  - made `no_plan` a valid non-executing result
  - made runtime stop before policy when planner output is invalid
  - made runtime validate `ToolRegistry` before policy authorization

## 2026-04-26 - Runtime Audit UI and Local CORS

- Added a minimal static Runtime Audit UI under:
  - `runtime_lab/runtime_audit_ui/frontend/index.html`
  - `runtime_lab/runtime_audit_ui/README.md`
- Kept the UI as an HTTP contract checker only:
  - calls `POST /agent/run`
  - calls `GET /tools`
  - calls `GET /health`
  - displays full backend JSON
  - does not choose tools
  - does not evaluate policy
  - does not modify runtime execution
  - does not call `runtime_lab/llm_lab`
- Added `GET /health` as an alias for the existing health route.
- Added local-dev-only CORS in `app/main.py` for Runtime Audit UI origins:
  - `http://127.0.0.1:8766`
  - `http://127.0.0.1:8767`
  - `http://localhost:8766`
  - `http://localhost:8767`
- Allowed CORS methods:
  - `GET`
  - `POST`
  - `OPTIONS`
- Allowed CORS headers:
  - `Authorization`
  - `Content-Type`
- Preserved runtime architecture boundaries:
  - no changes to `AgentService`
  - no changes to `AgentRuntime`
  - no changes to `Planner`
  - no changes to `PolicyEngine`
  - no changes to `ToolRegistry`
  - no changes to tools
  - no changes to `AgentResponse`
- Documented traceability gap:
  - `AgentResponse` does not expose a top-level `request_id`
  - any request ID inside `result` is tool-specific and not guaranteed by the
    public response contract
- Validated:
  - Python compile for modified FastAPI files
  - unittest discovery
  - browser preflight-equivalent `OPTIONS` requests from
    `http://127.0.0.1:8767`
  - `GET /health`
  - `GET /tools`
  - `POST /agent/run` with `dry_run=true`
