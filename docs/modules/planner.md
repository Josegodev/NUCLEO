# Planner

## Purpose
Transform an `AgentRequest` into an executable plan for the runtime.

## Real Behavior
The current planner performs minimal normalization on `request.user_input` and applies simple keyword-based rules.

Behavior:
1. Normalize input with `strip().lower()`
2. If the text contains `system` or `info`, return:
   - tool: `system_info`
   - payload: `{}`
3. Otherwise, return:
   - tool: `echo`
   - payload: `{"text": request.user_input}`

## Strengths
- Deterministic
- Easy to understand
- Clear separation from runtime and tools
- No side effects

## Issues Detected
- Plan output contract is implicit (`dict`)
- Matching logic is too weak and substring-based
- English-only keyword assumptions
- Tight coupling to literal tool names
- No explicit handling for empty input
- No decision traceability
- Payload/tool compatibility is implicit
- Universal fallback to `echo` is assumed safe but not formalized

## Risk Level
Medium

## Recommended Improvements
- Introduce typed execution plan schema
- Add reasoning or trace metadata for rule matches
- Formalize commands or intent rules
- Clarify or extend language support
- Handle empty input explicitly
- Reduce string-based coupling with tool names
- Prepare for rule-table or declarative routing growth

