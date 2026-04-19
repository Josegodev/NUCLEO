# ToolRegistry

## Layer

Verified architecture

## Purpose

Resolve production tools by name from the current in-memory production registry.

## Verified Current Behavior

`ToolRegistry` stores tool instances in a dictionary keyed by `tool.name`.

Supported operations:

- `register(tool)`
- `get(tool_name)`
- `list_tools()`

## Important Distinction

This registry is the production registry. It is separate from:

- `runtime_lab/`
- staging registry
- proposal store
- generated tool skeletons

Generated lab tools are not auto-registered here.

## Current Limitations

- duplicate names overwrite silently
- tool contract is not strongly validated at registration time
- runtime mutation and bootstrap-time mutation are not clearly separated

## Status Label

- Production registry: implemented
- Staging / promotion integration: not implemented in production registry
