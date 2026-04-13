cat > ARCHITECTURE.md << 'EOF'
# Architecture

## System Overview

This project is a modular agent backend built with FastAPI.

It receives a request, decides which tool to use, validates execution, executes the tool, and returns a structured response.

---

## Flow

Request → API → Runtime → Planner → PolicyEngine → ToolRegistry → Tool → Response

---

## Components

### API
- Entry point (FastAPI)
- Receives HTTP requests (/agent/run, /health)
- Translates JSON into internal schemas

### Runtime (Orchestrator)
- Central coordinator of the system
- Executes the full flow:
  Request → Planner → Policy → Tool → Response
- Ensures controlled and predictable execution

### Planner
- Maps user input to a tool and payload
- Current implementation: simple rule-based logic
- Future: may evolve into more advanced planning

### Policy Engine
- Validates whether a tool execution is allowed
- Provides control and safety layer
- Future: risk-based decisions

### Tool Registry
- Registers available tools
- Resolves tools by name

### Tools
- Encapsulated capabilities of the agent
- Examples:
  - echo
  - system_info
- Only place where real actions happen

### Schemas
- Define data structures:
  - AgentRequest
  - AgentResponse
- Ensure consistency and validation

### Core
- Shared infrastructure (e.g. logging)
- Future: configuration, utilities

---

## Principles

- Explicit control over execution
- No implicit side effects
- Modular but simple design
- Separation of concerns
- No hidden state
- Incremental evolution (no big refactors)

---

## Current Limitations

- No execution trace (no tool_calls yet)
- No persistent memory
- Simple planner (no multi-step logic)
- Basic policy engine

---

## Future

- ExecutionContext (traceability and logging)
- Tool metadata (risk, permissions)
- Multi-step planning
- Stronger policy rules
- Agent layer (agent.py as higher-level interface)

EOF