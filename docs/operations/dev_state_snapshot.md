# System Snapshot – NUCLEO

## Purpose

This document captures the current operational state of the system
at the moment of migration to a new Linux environment.

It reflects real implementation status and recent structural changes.

---

## System Overview

The system is a modular agent runtime built with FastAPI.

Execution pipeline (current implementation):

AgentRequest
→ AgentService
→ AgentRuntime
→ Planner
→ PolicyEngine
→ ToolRegistry
→ Tool
→ AgentResponse

---

## Current Architecture

- `api/` → HTTP routes (FastAPI)
- `runtime/` → execution orchestration
- `policies/` → execution control
- `tools/` → executable tools
- `schemas/` → data models

---

## Recent Refactor

### Tools restructuring

- `tools/local/` → local execution
- `tools/remote/` → reserved (not implemented yet)
- removed `tools/implementations/`

### New layers introduced

- `clients/` → planned external communication layer (not active)
- `audit/` → planned logging and traceability (not active)
- `runtime/dispatcher.py` → present but not integrated in execution flow

---

## Tools (current)

### echo_tool
- read_only: true
- simple echo behavior

### system_info_tool
- read_only: true
- returns system metadata

Both:
- registered in ToolRegistry
- callable via `/agent/run`

---

## Endpoints

### GET /tools
Returns list of registered tools

### POST /agent/run
Executes agent runtime

Example:

```json
{
  "user_input": "system info",
  "dry_run": true
}

