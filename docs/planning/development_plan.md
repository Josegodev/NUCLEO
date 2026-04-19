# Development Plan - NUCLEO

## Purpose

Define the next technical steps from the currently verified repository state without presenting future goals as implemented behavior.

## Current Base

Verified today:

- stable production runtime path
- request-scoped authentication with execution context
- structured `result` preserved in response
- isolated experimental lab for tool proposal and skeleton generation

## Current Priorities

### Priority 1 - Contract Reinforcement

Objective:
Reduce implicit contracts in production runtime.

Actions:

- introduce typed execution plan
- define stronger tool payload contracts
- define stronger tool result contract
- strengthen `BaseTool`

### Priority 2 - Execution Control

Objective:
Make execution semantics safer and more explicit.

Actions:

- enforce meaningful `dry_run`
- use `read_only` and `risk_level` in policy decisions
- prepare payload-aware restrictions

### Priority 3 - Runtime Robustness

Objective:
Make the production runtime resilient under failure.

Actions:

- add controlled exception handling by pipeline stage
- standardize error responses
- improve domain-level traceability

### Priority 4 - Composition Cleanup

Objective:
Separate bootstrap from orchestration.

Actions:

- inject planner, policy engine, and registry into runtime
- move composition logic out of orchestrator module
- prepare a dedicated bootstrap layer

### Priority 5 - Experimental Lab Maturation

Objective:
Make the lab path reviewable and operationally clearer without promoting it to production.

Actions:

- improve proposal schema quality
- improve staging review workflow
- improve generated artifact metadata
- add explicit approval/promotion design without activation

## Explicitly Future, Not Current

The following are not current production capabilities:

- real LLM-backed planning
- autonomous tool activation
- production self-extension
- dynamic package installation
- arbitrary shell execution
- production memory/state orchestration

## Guiding Principle

Stabilize before expanding.

The production runtime should become more explicit and controlled before experimental capabilities become more ambitious.
