cat > ARCHITECTURE.md << 'EOF'
# Architecture Vision

## Purpose

This document describes the intended architecture of the system.

It represents the target design and may differ from the current implementation.

For verified behavior, see:
`docs/architecture.md`

---

## System Overview

This project is a modular agent backend built with FastAPI.

The goal is to:
- receive a request
- decide which tool to use
- validate execution
- execute the tool
- return a structured response

---

## Target Flow

Request → API → AgentService → Runtime → Planner → PolicyEngine → ToolRegistry → Tool → Response

---

## Components (Target Design)

### API
- FastAPI entrypoint
- Handles HTTP transport
- Delegates to AgentService

### AgentService
- Stable application layer
- Entry point for execution
- Decouples API from runtime

### Runtime (Orchestrator)
- Central coordinator of execution
- Executes:
  Planner → Policy → Tool → Response

### Planner
- Maps user input to tool + payload
- Target: structured and extensible planning logic

### Policy Engine
- Controls execution permissions
- Target:
  - payload-aware rules
  - risk-based decisions
  - dry_run enforcement

### Tool Registry
- Maintains tool catalog
- Resolves tools by name

### Tools
- Encapsulated execution units
- Target:
  - structured input/output
  - metadata-driven behavior

### Schemas
- Define input/output contracts
- Target:
  - strict validation
  - typed execution structures

### Core
- Shared infrastructure
- Target:
  - logging
  - configuration
  - execution context

---

## Principles

- Explicit control over execution
- No implicit side effects
- Separation of concerns
- Strong contracts between components
- Incremental evolution

---

## Known Gaps vs Current Implementation

- Contracts between components are still implicit
- `dry_run` is not structurally enforced
- Tool outputs are not structured
- Runtime does not handle execution errors
- Policy is based on simple tool-name allowlist

---

## Target Capabilities

- ExecutionContext (traceability and logging)
- Structured tool input/output contracts
- Payload-aware policy rules
- Risk-based execution control
- Multi-step planning
- Optional LLM-assisted planning
- Memory/state handling (later stage)