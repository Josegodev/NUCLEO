# ToolGenerationService

## Responsibility

`ToolGenerationService` converts an experimental proposal into lab-only artifacts:

- Python tool skeleton
- Placeholder test file
- Minimal metadata

## Output

Artifacts are written under `runtime_lab/generated_tools/<tool_name>/`.

## Notes

- Generated files are not auto-registered in production.
- Output is intended for review, not direct execution rollout.
- Generation is audited.
