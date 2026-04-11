## app/main.py

### Purpose
Application entrypoint for the FastAPI server.

### Current responsibility
- Create FastAPI app
- Register API routers
- Expose HTTP interface

### What it should not do
- Agent execution logic
- Planning logic
- Policy logic
- Tool execution
- Business rules

### Current maturity
Simple and correct

### Future evolution
- Add API metadata
- Add startup/shutdown hooks if needed
- Keep routing only, avoid logic growth

## app/api/routes/agent.py

### Purpose
HTTP entrypoint for agent execution.

### Current responsibility
- Receive POST /agent/run requests
- Validate input via AgentRequest
- Call AgentRuntime
- Return AgentResponse

### What it should not do
- Planning logic
- Policy logic
- Tool execution logic
- Business rules

### Current maturity
Simple and correct

### Risks
- Runtime instantiated globally (no dependency injection)

### Future evolution
- Dependency injection for runtime
- Logging and tracing
- Authentication layer

## app/runtime/orchestrator.py

### Purpose
Central execution coordinator of the agent runtime.

### Current responsibility
- Receive AgentRequest
- Ask planner for tool + payload
- Ask PolicyEngine whether execution is allowed
- Resolve tool via ToolRegistry
- Execute tool
- Return AgentResponse

### What it should not do
- HTTP handling
- Tool implementation logic
- Planner logic
- Deep business rules

### Current maturity
Functional and well-oriented, but still basic

### Strengths
- Clear execution flow
- Separation between planning, policy, and tool execution
- Controlled execution through policy layer

### Current limitations
- Uses global dependencies
- No execution tracing
- Response structure is too simple
- No robust error handling
- Policy logic is still basic

### Future evolution
- Add minimal logging
- Return structured tool output
- Add controlled error handling
- Introduce execution context later
- Move to dependency injection when needed

# Files Audit

## app/main.py
- Entry point (FastAPI)
- Registers routers

## app/api/routes/agent.py
- HTTP interface for agent
- Calls AgentRuntime

## app/runtime/orchestrator.py
- Coordinates execution flow
- Planner → Policy → Tool → Response

## Next
- app/runtime/planner.py (pending)