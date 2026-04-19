# Repo Audit

## Layer

Audit

## Purpose

Evaluate repository structure, module boundaries, naming consistency, and fit between physical layout and architectural intent.

## Current Repository Shape

High-level structure verified in the repository:

- `app/`
- `docs/`
- `docs_esp/`
- `runtime_lab/`

### Application structure

- `api/` -> HTTP routes and auth boundary
- `services/` -> service-layer and lab services
- `runtime/` -> orchestration and planning
- `policies/` -> execution control
- `tools/` -> production tools
- `schemas/` -> request, response, and experimental schemas
- `domain/` -> lab domain entities

### Documentation structure

- `docs/architecture.md` -> verified architecture
- `docs/vision/` -> target vision
- `docs/operations/` -> operational state and session logs
- `docs/audits/` -> audits
- `docs/modules/` -> per-module documentation
- `docs/planning/` -> development roadmap

### Experimental runtime-lab structure

- `runtime_lab/proposals/`
- `runtime_lab/generated_tools/`
- `runtime_lab/staging_registry/`
- `runtime_lab/audit/`

## Structural Strengths

- Clear separation between production runtime and lab artifacts
- Reasonable package boundaries for current scale
- Documentation structure can support multiple documentary layers

## Structural Risks

- Production runtime composition is still embedded in runtime module
- `docs_esp/` is now maintained as a translation tree, but can still drift if updates are not synchronized
- `runtime_lab/` persistence is operationally separate but still colocated in repo workspace

## Naming Assessment

Current primary names are coherent and should remain stable:

- runtime
- orchestrator
- planner
- policy engine
- tool registry
- tool
- staging
- audit
- proposal
- lab / runtime_lab

## Overall Assessment

The repository is still structurally coherent, but documentation drift and import-time composition remain the main architecture-level risks rather than raw directory disorder.
