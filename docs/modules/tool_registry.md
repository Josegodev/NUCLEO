# ToolRegistry

## Layer

Verified architecture

## Purpose

Resolve production tools by name from the current in-memory production registry.

## Verified Current Behavior

`ToolRegistry` stores production tool instances keyed by `tool.name`, but it is
no longer just an unchecked dictionary. Registration validates the tool against
the production contract boundary.

Supported operations:

- `register(tool)`
- `get(tool_name)`
- `list_tools()`
- `list_contracts()`

Registration requires:

- the object inherits `BaseTool`
- the tool name is inside the closed production tool set
- the tool exposes a `ToolContractArtifact`
- the contract name matches `tool.name`
- the name has not already been registered

## Important Distinction

This registry is the production registry. It is separate from:

- `runtime_lab/`
- staging registry
- proposal store
- generated tool skeletons

Generated lab tools are not auto-registered here.

## Current Limitations

- runtime mutation and bootstrap-time mutation are not clearly separated

## Status Label

- Production registry with contract validation: implemented
- Staging / promotion integration: not implemented in production registry
