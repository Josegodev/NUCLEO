# Architecture Vision

## Purpose

This document describes the target architecture of NUCLEO. It is intentionally future-oriented and must not be read as a statement of verified current behavior.

For implemented behavior, see:

- `docs/architecture.md`

## Target Direction

NUCLEO should evolve toward a modular agent runtime with:

- explicit internal contracts
- controlled execution semantics
- typed execution planning
- richer policy enforcement
- auditable orchestration
- isolated experimental surfaces for LLM-assisted capability growth

## Target Flow

Request  
→ API  
→ AgentService  
→ Runtime  
→ Planner  
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse

The target shape preserves the stable pipeline, but strengthens contract quality and operational control at each stage.

## Target Component Design

### API

- Transport boundary only
- Authentication and request validation at edge
- No business execution logic

### AgentService

- Stable application entrypoint
- Runtime facade
- Future tracing and orchestration hooks

### Runtime

- Central orchestration layer
- Explicit plan handling
- Controlled failure semantics
- Isolated branching between production runtime and experimental lab flows

### Planner

- Evolve from ad hoc rules to more explicit planning structures
- Support declarative rules first
- Support optional LLM-assisted proposal logic later
- Never become the final authority for execution

### PolicyEngine

- Move from name-based checks to metadata-aware and payload-aware control
- Enforce meaningful `dry_run`
- Preserve deny-by-default behavior

### ToolRegistry

- Keep production registry distinct from staging or lab registries
- Strengthen registration contracts and metadata validation

### Tools

- Typed input/output contracts
- Clear metadata semantics
- Safer execution boundaries

### Experimental Lab

- Remain isolated from production runtime
- Support proposal generation, skeleton generation, staging review, and auditability
- Never auto-promote to production without explicit review

## Design Principles

- explicit control over execution
- no hidden authority shifts toward models or generated artifacts
- separation of concerns
- stable production path
- isolated experimental path
- traceability before autonomy

## Known Gap Between Current State and Vision

Current code already contains a first experimental lab path, but the target architecture is still not complete. In particular, the following remain future or partial:

- typed execution plan
- strict runtime plan validation
- full dry-run enforcement
- payload-aware policy
- complete traceability of production execution
- real LLM-backed planning under controlled conditions
- formal promotion workflow from staging to production
