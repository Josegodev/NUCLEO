# ToolRegistry

## Purpose
Central registry of available tools in the system.

## Real Behavior
`ToolRegistry` stores tool instances in an internal dictionary keyed by `tool.name`.

Behavior:
- `register(tool)`: stores the tool under its name
- `get(tool_name)`: returns the matching tool or `None`
- `list_tools()`: returns all registered tool instances

## Strengths
- Simple and efficient dictionary-based lookup
- Clear separation of responsibility
- Appropriate complexity for a small bootstrap system
- Easy to understand and test

## Issues Detected
- Duplicate tool names silently overwrite previous registrations
- No strict runtime validation of tool type or tool name
- Tool name contract is implicit but critical
- `get()` delegates missing-tool handling downstream
- `list_tools()` exposes live tool instances
- No metadata-oriented introspection support
- No distinction between bootstrap-time and runtime mutation

## Risk Level
Medium

## Recommended Improvements
- Reject duplicate registrations
- Validate tool contract at registration time
- Type internal storage explicitly
- Document the `get()` missing-tool behavior
- Add helper methods such as `has()` or `list_tool_names()`
- Prepare registry usage for metadata-based policy and documentation

