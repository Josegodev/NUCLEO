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
