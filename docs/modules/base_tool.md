# BaseTool

## Purpose
Define the common interface and metadata required for all tools in the system.

## Real Behavior
`BaseTool` defines attributes and a `run(payload)` method that must be implemented by concrete tools.

However:
- It is not an abstract class
- Metadata is not validated
- There is no enforced contract for inputs or outputs

## Strengths
- Provides a common conceptual structure
- Separates tools from runtime
- Simple and easy to extend

## Issues Detected
- Not a true interface (can be instantiated directly)
- Metadata fields are not enforced or validated
- `risk_level` is an untyped string
- `read_only` is not enforced anywhere
- Output contract of `run()` is unclear
- No payload schema or validation
- No support for `dry_run`
- Tool identity relies only on a string name

## Risk Level
Medium-High

## Recommended Improvements
- Convert into an abstract base class
- Validate metadata at initialization
- Introduce a typed `RiskLevel`
- Standardize tool output format
- Define payload schemas per tool
- Add support for `dry_run` or execution context
- Prepare separation between metadata and execution logic

TEST_SAVE_ARCHITECTURE_130426