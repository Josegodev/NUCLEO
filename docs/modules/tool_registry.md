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

## Impact on LLM Augmentation

`ToolRegistry` is now also the source of truth for the tool contract catalog
shown to the Planner augmentation prompt.

`build_tool_contract_prompt(tool_registry)` reads:

```text
tool_registry.list_contracts()
```

and renders the registered tool names plus their required argument fields. This
keeps the prompt aligned with the same contracts used later by runtime
validation.

Important boundary:

- `ToolRegistry` does not call LLM providers
- `ToolRegistry` does not execute from prompt content
- `ToolRegistry` does not accept tool names from `/agent/approve`
- execution still requires runtime orchestration, `PolicyEngine`, payload
  validation, and then `tool.run(...)`

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
