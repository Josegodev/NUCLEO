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
- `contract`
- `validate_input(payload)`
- `validate_output(output)`
- `run(payload, context=None)`

Concrete tools are expected to implement `run(...)`.

`contract` must be a `ToolContractArtifact` and includes:

- tool name
- input schema
- output schema
- preconditions
- postconditions
- explicit side effects
- version

## Important Current Reality

- `BaseTool` is not a strict abstract base class
- metadata is not validated at construction time
- metadata is not yet enforced by policy
- input/output contracts are explicit for registered production tools

## Status Label

- Common tool contract concept: implemented
- Strong typed contract enforcement at registry/runtime boundary: implemented
