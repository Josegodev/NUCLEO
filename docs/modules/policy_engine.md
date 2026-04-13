# PolicyEngine

## Purpose
Validate whether a planned tool execution is allowed before reaching the execution stage.

## Real Behavior
The current policy engine applies a static whitelist by tool name.

Behavior:
- Allows `echo`
- Allows `system_info`
- Denies any other tool
- Ignores `payload`
- Ignores `dry_run`

Returns a `PolicyDecision` with:
- `decision`: `allow` or `deny`
- `reason`: explanatory string

## Strengths
- Real deny-by-default behavior
- Simple and auditable
- Clear separation from execution
- Structured output via `PolicyDecision`

## Issues Detected
- `payload` is not evaluated
- `dry_run` has no effect on policy decisions
- Security is based only on tool name, not capability or metadata
- Hardcoded tool names create duplication with planner/registry
- No structured policy rule identifiers
- Not ready for contextual or parameter-sensitive control

## Risk Level
Medium

## Recommended Improvements
- Document explicitly that this is currently a tool-name allowlist
- Start using tool metadata such as `read_only` and `risk_level`
- Enforce meaningful `dry_run` restrictions
- Prepare payload-aware validation
- Move toward declarative rule definitions
- Enrich `PolicyDecision` with rule metadata

