# NUCLEO Context Snapshot

Generated at: 2026-04-25T17:14:44+00:00

## Scope

- Project: NUCLEO
- Phase: HARDENING
- LLM role: external observer only
- Runtime integration: none
- Forbidden actions: execute tools, modify runtime, bypass policy, call agent API

## Architecture Flow

API -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> Tool

## Open HARDENING Topics

- closed policy decisions
- dry_run determinism
- structured AgentResponse
- policy/registry consistency
- error handling
- observability

## Files Included

- `README.md` (5325 bytes, sha256: `fe87c06511e62cf856a4d808a023a3f4b89eb0c2ecc5b713e993b2d724293f69`)
- `docs/architecture.md` (5789 bytes, sha256: `b721e98907eb9c0c994f59888ab14a4ef9e725f0d200d2065eb11a01819f7319`)
- `docs/operations/operational_state.md` (4424 bytes, sha256: `a4c658760e5052ffee9e2fc8e3cf71fd8f0f7bf2865dddd7100700d488c68202`)
- `docs/operations/session_log.md` (5576 bytes, sha256: `a5779fb88641ffedf9da9a4ae5bf0687505cfaecdac4c757674ad3e45e382efd`)
- `docs/modules/agent_service.md` (750 bytes, sha256: `c7e7b03b256e8fa270e93721c124ed4a37028dc07c18ede9989a70712806fb03`)
- `docs/modules/audit_store.md` (420 bytes, sha256: `c66f5fe73a6c99ddaa14fb8ca3ddc1760fd0d44bd57f1104a3192ae8675dd542`)
- `docs/modules/base_tool.md` (646 bytes, sha256: `691a546cb9aa28214a0aacdae00e20b7ec1b39a56aaa45a70e1cb2826ff8842d`)
- `docs/modules/orchestrator.md` (2011 bytes, sha256: `9c65f9b6f8425526c1e855fcada4a92a6bb40810b6758f105566be05053c2b37`)
- `docs/modules/planner.md` (1283 bytes, sha256: `d0dd522d5cecdc434f743b3b7082fee07480753171dc44a686e71abfc1aa8dd6`)
- `docs/modules/policy_engine.md` (977 bytes, sha256: `0f5b68468be1057860f4c76f7e6b98da107483688f401d85f703e57fb707187d`)
- `docs/modules/staging_registry.md` (440 bytes, sha256: `16ded85cfc81795eb96827b6639154c91bb9ccd0b530a01a7e2470c581504dbc`)
- `docs/modules/tool_generation_service.md` (434 bytes, sha256: `82fdafb585748b8ba029bca3cd4e31153e214014758e8d41c2459d35f8a91778`)
- `docs/modules/tool_proposal_service.md` (675 bytes, sha256: `4ec5f129c77c3abaa0f50b7a8569c96930fec649f05052d0d36194efb39e1e9c`)
- `docs/modules/tool_registry.md` (874 bytes, sha256: `8f43370c32cf6c37fa90ca4c50a7aafc43ab44e64307a49625f9897bf1508d35`)

## Context

### README.md

```text
# NUCLEO

NUCLEO es un runtime de agentes modulares construido sobre FastAPI. Su objetivo es ejecutar peticiones de usuario mediante un pipeline controlado y auditable, evitando comportamientos opacos y separando con claridad decisión, validación y ejecución.

## Estado documental

La documentación del repositorio sigue esta convención:

- `docs/architecture.md` describe arquitectura verificada en código.
- `docs/vision/architecture_vision.md` describe arquitectura objetivo.
- `docs/operations/` recoge estado operativo y session logs.
- `docs/audits/` recoge evaluaciones críticas y consistencia documental.

Si un documento describe una capacidad futura o experimental, debe indicarlo explícitamente.

## Arquitectura verificada

El flujo estable actual es:

Request  
→ API  
→ AgentService  
→ AgentRuntime  
→ Planner  
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse

### Componentes verificados

- `Planner` adapta intención a una acción candidata determinista.
- `ToolRegistry` es la fuente de verdad de tools ejecutables.
- `PolicyEngine` autoriza la ejecución según autenticación, rol y nombre de tool.
- `Tool` ejecuta la acción real.
- `AgentResponse` devuelve `status`, `message` y `result` opcional.

## Estado actual del runtime

### Implementado actualmente

- API FastAPI funcional
- Endpoint `POST /agent/run`
- Endpoint `GET /tools`
- Endpoint `GET /`
- Autenticación por API key por request
- `ExecutionContext` propagado por runtime, policy y tools
- Tools de producción:
  - `echo`
  - `system_info`
  - `disk_info`
- Resultado estructurado conservado en `AgentResponse.result`
- Fase HARDENING en curso:
  - contratos runtime-policy-registry más explícitos
  - Planner devuelve `planned` o `no_plan`
  - `no_plan` no ejecuta tools
  - `dry_run` no ejecuta la tool real
  - trazabilidad interna mínima en memoria para el runtime

### Experimental, no producción

Existen módulos y artefactos de laboratorio aislados en `runtime_lab/`, pero no
forman parte del contrato estable actual del Planner. El Planner estable solo
devuelve `planned` o `no_plan`.

### LLM Lab / Ruta lateral experimental

`runtime_lab/llm_lab/` vive dentro del repositorio para facilitar observación y
consultas locales con Mistral/Qwen, pero no está integrado en el runtime de
NUCLEO.

Propósito:

- cargar contexto documentado de NUCLEO para revisión externa
- ejecutar chats locales de laboratorio con SQLite y Ollama
- generar informes markdown de revisión HARDENING

Estado actual:

- experimental
- ruta lateral de solo observación respecto al runtime productivo
- sin integración con `AgentService`, `AgentRuntime`, `Planner`,
  `PolicyEngine`, `ToolRegistry` ni `Tools`

Prohibido para esta ruta:

- ejecutar tools de producción
- modificar policy
- llamar automáticamente a `/agent/run`
- actuar como Planner
- registrar tools en el `ToolRegistry` de producción

Referencia operativa: `docs/operations/operational_state.md`.

### No implementado todavía

- Integración real con LLM para planificación
- Integración de Mistral/Qwen en el flujo canónico
- Promoción automática desde staging a producción
- Ejecución de tools generadas en el registry principal
- Persistencia operativa del runtime más allá de artefactos de laboratorio
- Exposición pública de trazas por API
- Persistencia de trazas fuera de memoria

## Quick start:

source .venv/bin/activate

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar el servidor

```bash
uvicorn app.main:app --reload
```

### 3. Abrir Swagger

```text
http://127.0.0.1:8000/docs
```

## Autenticación

El sistema utiliza API key por request mediante `Authorization: Bearer <token>`.

Clave de desarrollo disponible en la configuración actual:

- `dev-jose-key`

## Ejemplo de uso

### Request

```json
{
  "user_input": "system info",
  "dry_run": true
}
```

### curl

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Authorization: Bearer dev-jose-key" \
  -H "Content-Type: application/json" \
  -d "{\"user_input\": \"system info\", \"dry_run\": true}"
```

### Response actual

```json
{
  "status": "dry_run_success",
  "message": "{'dry_run': True, 'executed': False, 'tool': 'system_info', 'payload': {}}",
  "result": {
    "dry_run": true,
    "executed": false,
    "tool": "system_info",
    "payload": {}
  }
}
```

En `dry_run=true`, el runtime ejecuta Planner, PolicyEngine y ToolRegistry,
pero no llama a `Tool.run(...)`. La respuesta indica la tool que se habría
ejecutado y marca `executed=false`.

## Flujo de ejecución

Cliente HTTP  
↓  
Uvicorn  
↓  
FastAPI (`/agent/run`)  
↓  
AgentService  
↓  
AgentRuntime  
↓  
Planner → PolicyEngine → ToolRegistry → Tool / dry_run  
↓  
AgentResponse

Si el Planner devuelve `no_plan`, el Runtime no consulta PolicyEngine y no
ejecuta ninguna tool. El Planner no autoriza y no ejecuta; solo propone.

La trazabilidad de ejecución existe como mecanismo interno en memoria del
runtime. No forma parte del contrato público de `/agent/run`, no se persiste y
no se expone todavía mediante endpoint.

## Referencias útiles

- `docs/architecture.md`
- `docs/vision/architecture_vision.md`
- `docs/EVOLUTION_MAP.md`
- `docs/audits/documentation_consistency_audit.md`

```

### docs/architecture.md

```text
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
- Acts as a deterministic intent-to-candidate-action adapter
- Returns a typed `PlannedAction`
- Does not authorize or execute tools
- Can emit either:
  - `planned`
  - `no_plan`

### PolicyEngine

- Requires authenticated execution context
- Allows `echo`
- Allows `disk_info`
- Allows `system_info` only for `admin`
- Denies all other production tools by name

### ToolRegistry

- Stores production tool instances in a dictionary
- Resolves tools by `tool.name`
- Is separate from staging and experimental registries

### LLM Lab / Experimental Side Path

`runtime_lab/llm_lab/` is present inside the repository, but it is not part of
the stable execution flow.

It may:

- load documented repository context for external review
- run local Mistral/Qwen chat scripts through Ollama
- persist local chat memory in SQLite files under `runtime_lab/llm_lab/`
- generate markdown HARDENING review reports under
  `runtime_lab/llm_lab/reports/`

It must not:

- call `AgentService` or `/agent/run` automatically
- act as Planner
- execute production tools
- modify `PolicyEngine`
- register tools in the production `ToolRegistry`

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
- `tool: str | None`
- `payload: dict | None`
- `dry_run: bool = True`
- `experimental_tool_generation: bool = False`

### Planner Output

The planner returns `PlannedAction`.

Current fields:

- `status`
- `tool_name`
- `payload`
- `confidence`
- `reason`
- `source`

`status` can be:

- `planned`
- `no_plan`

`no_plan` is a valid result. It means no deterministic rule matched, so runtime
must not execute any tool.

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

Experimental proposal and staging modules still exist in isolated code and
`runtime_lab/`, but they are not part of the current stable Planner contract.

The current Planner returns only:

- `planned`
- `no_plan`

The request field `experimental_tool_generation` exists in `AgentRequest`, but
the current stable runtime does not use it to branch into a capability-gap flow.

Experimental generated tools are not auto-registered in the production
`ToolRegistry`.

## Verified Constraints and Limitations

- Planner output is typed as `PlannedAction` and runtime-validated
- `dry_run` is structurally enforced by the runtime: policy is evaluated, the
  tool step is traced, and the production tool is not executed
- Policy is still largely name-based
- Tool metadata such as `read_only` and `risk_level` are not yet enforced by policy
- Production bootstrap still happens at module import time in `orchestrator.py`
- Error handling in runtime is still limited

## Explicitly Not Verified

The following must not be described as implemented production behavior:

- Real LLM-backed planning
- Mistral/Qwen participation in the production runtime
- Auto-extension of production registry
- Dynamic package installation
- Arbitrary shell execution
- Autonomous promotion from staging to production

Those behaviors are either not implemented or only documented as future direction elsewhere.

```

### docs/operations/operational_state.md

```text
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

```

### docs/operations/session_log.md

```text
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

```

### docs/modules/agent_service.md

```text
# AgentService

## Layer

Verified architecture

## Purpose

Provide a stable service-layer facade between API routes and runtime orchestration.

## Verified Current Behavior

`AgentService` currently:

- instantiates `AgentRuntime`
- exposes `run(request, context)`
- delegates execution directly to runtime

It does not currently own:

- planning
- policy
- tool execution
- lab proposal generation logic

## Strengths

- Keeps API thin
- Preserves a stable entrypoint
- Clean place for future tracing or orchestration hooks

## Current Limitations

- Runtime dependency is still constructed directly
- No independent error normalization boundary yet

## Status Label

- Service facade: implemented
- Dependency injection boundary: not implemented

```

### docs/modules/audit_store.md

```text
# AuditStore

## Responsibility

`AuditStore` persists simple structured audit events for the experimental tool-expansion
workflow.

## Event fields

- event
- timestamp
- proposal_id
- action
- result
- artifact_paths
- metadata

## Output

Each event is written as a JSON file under `runtime_lab/audit/`.

## Notes

- The store is append-only at this stage.
- Audit artifacts support review and post-hoc traceability.

```

### docs/modules/base_tool.md

```text
# BaseTool

## Layer

Verified architecture

## Purpose

Define the common conceptual interface for production tools.

## Verified Current Behavior

`BaseTool` currently declares:

- `name`
- `description`
- `read_only`
- `risk_level`
- `run(payload, context=None)`

Concrete tools are expected to implement `run(...)`.

## Important Current Reality

- `BaseTool` is not a strict abstract base class
- metadata is not validated at construction time
- metadata is not yet enforced by policy
- input/output contracts remain implicit

## Status Label

- Common tool contract concept: implemented
- Strong typed contract enforcement: not implemented

```

### docs/modules/orchestrator.md

```text
# AgentRuntime

## Layer

Verified architecture

## Purpose

Central execution orchestrator of the production runtime.

## Verified Current Behavior

`AgentRuntime.run(request, context)` currently:

1. starts an internal in-memory execution trace
2. asks the planner for a `PlannedAction`
3. records the planner step
4. validates that the planner returned `PlannedAction`
5. if the plan is `no_plan`, returns a controlled `no_plan` response
6. otherwise extracts candidate `tool_name` and `payload`
7. asks `PolicyEngine` for authorization
8. records the policy step
9. if denied, returns `blocked`
10. resolves the tool from production `ToolRegistry`
11. records the registry step
12. if missing, records the registry step as `error` and returns `error`
13. if `dry_run=True`, records a tool step as `skipped` with `executed=False` and does not run the tool
14. otherwise executes `tool.run(payload, context=context)`
15. records success or error for the tool step
16. returns `AgentResponse`

## Internal Trace Contract

Tracing is implemented in `app/runtime/tracing.py` and is intentionally
in-memory only.

`ExecutionTrace`:

- `trace_id`
- `request_id`
- `steps`

`ExecutionStep`:

- `step_id`
- `phase`: `planner`, `policy`, `registry`, or `tool`
- `input`
- `output`
- `status`: `success`, `denied`, `error`, or `skipped`
- `error`
- `timestamp`

Tracer failures are isolated from authorization and execution decisions. A
tracing failure must not cause a denied tool to execute and must not hide a real
tool error.

## Current Strengths

- Clear production pipeline
- Explicit policy check before production tool execution
- Explicit handling of missing production tool
- Minimal internal trace for planner, policy, registry, and tool stages

## Current Limitations

- Runtime composition still happens at import time
- Limited exception handling
- Response still duplicates data between `message` and `result`

## Status Label

- Production path: implemented
- Full contract hardening: not implemented

```

### docs/modules/planner.md

```text
# Planner

## Layer

Verified architecture

## Purpose

Transform an `AgentRequest` into a deterministic candidate action.

The planner proposes. It does not authorize, resolve runtime truth, or execute.

## Verified Current Behavior

The planner currently:

1. normalizes `request.user_input` with `strip().lower()`
2. if `request.tool` is set and the tool exists in `ToolRegistry`, returns `planned`
3. evaluates a small explicit table of deterministic rules
4. if a rule matches and its tool exists in `ToolRegistry`, returns `planned`
5. otherwise returns `no_plan`

## Contract Observed in Code

Current output is `PlannedAction`.

Fields:

- `status`
- `tool_name`
- `payload`
- `confidence`
- `reason`
- `source`

Statuses:

- `planned`
- `no_plan`

`no_plan` is expected when no deterministic rule matches.

## Strengths

- Deterministic
- Side-effect free in production path
- Easy to read
- Rules are table-driven and auditable
- Planner checks rule targets against `ToolRegistry`
- Runtime receives a typed contract instead of an implicit dict

## Current Limitations

- Matching logic is weak and heuristic-based
- Strong coupling to literal production tool names remains

## Status Label

- Production planning: implemented
- Real LLM-assisted planning: not implemented

```

### docs/modules/policy_engine.md

```text
# PolicyEngine

## Layer

Verified architecture

## Purpose

Validate whether a planned production tool execution is allowed before reaching the execution stage.

## Verified Current Behavior

`PolicyEngine.evaluate(...)` currently:

- denies unauthenticated requests
- allows `echo`
- allows `disk_info`
- allows `system_info` only when `admin` is present in roles
- denies any other tool name

It returns a `PolicyDecision` with:

- `decision`
- `reason`

## What It Does Not Currently Do

- it does not deeply evaluate payload
- it does not make different decisions for `dry_run`; runtime enforces non-execution
- it does not use `read_only` or `risk_level`
- it does not govern lab artifact generation directly

## Strengths

- deny-by-default shape
- clear separation from execution
- authenticated context is part of decision path

## Status Label

- Production authorization: implemented
- Metadata-aware policy: not implemented
- Lab promotion control: not implemented

```

### docs/modules/staging_registry.md

```text
# StagingRegistry

## Responsibility

`StagingRegistry` is a JSON-backed isolated registry for experimental proposals.

## Supported statuses

- `draft`
- `generated`
- `reviewed`
- `approved`
- `rejected`

## Persistence

Registry state is stored in `runtime_lab/staging_registry/registry.json`.

## Notes

- This registry is intentionally separate from `app/tools/registry.py`.
- Approval in staging does not imply production activation.

```

### docs/modules/tool_generation_service.md

```text
# ToolGenerationService

## Responsibility

`ToolGenerationService` converts an experimental proposal into lab-only artifacts:

- Python tool skeleton
- Placeholder test file
- Minimal metadata

## Output

Artifacts are written under `runtime_lab/generated_tools/<tool_name>/`.

## Notes

- Generated files are not auto-registered in production.
- Output is intended for review, not direct execution rollout.
- Generation is audited.

```

### docs/modules/tool_proposal_service.md

```text
# ToolProposalService

## Responsibility

`ToolProposalService` creates deterministic experimental proposals from an
explicit caller-provided proposal request. The current stable Planner does not
call this service and does not emit `capability_gap_detected`.

The current version does not call a real LLM; it acts as a stable placeholder
that emits structured proposal JSON.

## Output

The service writes proposal artifacts to `runtime_lab/proposals/<proposal_id>.json`.

## Notes

- The proposal is descriptive, not executable.
- Proposal generation is audited.
- The service is isolated from the production registry.
- It is not connected to the stable `/agent/run` flow.

```

### docs/modules/tool_registry.md

```text
# ToolRegistry

## Layer

Verified architecture

## Purpose

Resolve production tools by name from the current in-memory production registry.

## Verified Current Behavior

`ToolRegistry` stores tool instances in a dictionary keyed by `tool.name`.

Supported operations:

- `register(tool)`
- `get(tool_name)`
- `list_tools()`

## Important Distinction

This registry is the production registry. It is separate from:

- `runtime_lab/`
- staging registry
- proposal store
- generated tool skeletons

Generated lab tools are not auto-registered here.

## Current Limitations

- duplicate names overwrite silently
- tool contract is not strongly validated at registration time
- runtime mutation and bootstrap-time mutation are not clearly separated

## Status Label

- Production registry: implemented
- Staging / promotion integration: not implemented in production registry

```
