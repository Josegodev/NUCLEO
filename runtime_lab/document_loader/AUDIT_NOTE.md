# Audit Note: Why This Is Not A NUCLEO Tool

Classification: INFORMATIVO

`runtime_lab/document_loader` is a local experimental ingestion lab. It is not a
NUCLEO Tool because it is not part of the production execution contract.

## Boundary Check

This lab does not:

- subclass `BaseTool`
- register in `ToolRegistry`
- call `AgentRuntime`
- call `Planner`
- call `PolicyEngine`
- produce or consume `PolicyDecision`
- expose an API route
- execute from `AgentService`

The current implementation only validates an operator-provided PDF path and
writes deterministic lab artifacts for future local parser output:

- JSONL records
- manifest JSON
- local LLM context Markdown

These artifacts are files for external observers. They are not execution
authority inside NUCLEO.

## LLM Consumption Boundary

Mistral, Qwen, and Ollama may later read the generated `.context.md` file as
plain text context. That consumption remains external observer activity because
the document loader:

- does not call any LLM
- does not call network services
- does not inject context into `AgentRuntime`
- does not let model output influence `PolicyEngine`
- does not let model output register or execute `Tools`

The context Markdown is read-only input for local experiments, not a runtime
decision source.

## Why Contract Comes Before Parser

The parser contract comes before parser integration because extraction libraries
turn untrusted PDF bytes into structured records. Without a contract, NUCLEO
would not know whether a parser result is valid, incomplete, malformed, or
invented.

The validator prevents these failure modes before any real parser is added:

- invalid JSONL lines
- records missing required fields
- unsupported `block_type` values
- mismatched `content_hash`
- mixed `document_id` values in one JSONL file
- empty output being accepted without the explicit `no parser integrated` state
- manifest record counts drifting from JSONL record counts

## Why OpenDataLoader Is Still Premature

OpenDataLoader-style integration remains PREMATURO because the current lab has
not closed parser limits, malformed PDF behavior, page limits, file size limits,
or the future Tool error schema. Adding a parser before those decisions would
increase behavior surface before the contract is stable.

## Why Limits Come Before Parser Integration

Limits come before parser integration because a PDF parser receives untrusted
bytes. If the lab accepts any path, any size, or any future page count, the
parser contract starts with ambiguous behavior.

Current hardening defaults live in `loader_config.py`:

- `MAX_PDF_BYTES`
- `MAX_PAGES`
- `ALLOWED_INPUT_ROOTS`
- `DEFAULT_OUTPUT_ROOT`
- `PARSER_STATUS_NO_PARSER`

These limits reduce future `PolicyEngine` ambiguity. A future Tool should not
need to guess whether a failed parse was unauthorized input, invalid file type,
oversized content, parser failure, or a policy denial. Each case now has a
separate normalized error path before parser integration.

## Why Parser Execution Limits Come Before OpenDataLoader

Parser execution limits must exist before OpenDataLoader or any other parser is
integrated because parser output can be large, slow, malformed, or unexpectedly
fragmented. The lab now defines timeout, record count, per-record content, and
total-content limits before any parser is allowed to emit records.

## Why Silent Truncation Is Forbidden

Silent truncation means shortening content without recording that it happened.
That is forbidden because it makes downstream local LLM context look complete
when it is not. If content exceeds a limit, the correct behavior is a normalized
error such as `content_record_too_large` or `content_total_too_large`.

This prevents future runtime ambiguity: a future Tool should return a clear
failure instead of returning partial content that `AgentRuntime`, `PolicyEngine`,
or a caller might mistake for complete parser output.

## Why Adapter Comes Before Parser

The adapter comes before parser integration because the loader needs a stable
boundary before it depends on OpenDataLoader or any other PDF library.

The current boundary is:

- `BasePdfParser`
- `ParserResult`
- `ParserError`
- `NoOpPdfParser`

This reduces coupling to OpenDataLoader. A future OpenDataLoader integration
should live behind an adapter and return the same `ParserResult` shape.

This also prevents parser-specific behavior from leaking into a future
`ToolRegistry` entry. If NUCLEO ever promotes document loading into a Tool, the
Tool should depend on the stable adapter contract, not on OpenDataLoader
internals, exception types, or output quirks.

## Real PDFs As Smoke Inputs

Local real PDFs may be useful for operational smoke testing, but they are not
contract fixtures. They should remain local inputs unless they are explicitly
approved and placed under a fixtures policy.

Contract fixtures should be small, deterministic, and reviewable. Real PDFs can
carry licensing, privacy, size, and reproducibility concerns, so the batch smoke
runner treats them as local operator inputs only.

## Why Tests Use Synthetic Inputs

The unit tests use synthetic JSONL fixtures and temporary files because they are
small, deterministic, and safe to review. This keeps the contract tests focused
on schema, validation, adapter behavior, and loader error handling.

Real PDFs remain operational smoke inputs only. They are useful for manual or
local batch checks, but they may contain licensed, private, large, or unstable
content. They should not become test fixtures without explicit approval.

These tests are still not parser integration. `NoOpPdfParser` remains the active
parser adapter, and no extraction results are invented.

## Why Disabled OpenDataLoader Adapter Is Not Integration

Current status: adapter stub exists, disabled.

The OpenDataLoader adapter is only a disabled stub. It does not load the
OpenDataLoader package, does not parse PDFs, does not add a dependency, and is
not used by `load_pdf_to_jsonl.py` by default.

This reduces future coupling because the intended integration point is now the
adapter contract, not OpenDataLoader internals. The loader continues to depend
on `ParserResult`, normalized errors, and JSONL validation.

Activation requires completing `PARSER_ACTIVATION_CHECKLIST.md`.

Before enabling the adapter, these items must be reviewed:

- dependency version and license
- malformed PDF behavior
- timeout enforcement
- page count enforcement
- record and content limit enforcement
- parser exception mapping into `ERROR_MODEL.md`
- deterministic fixtures for parser output
- whether outputs may contain sensitive content

Even after activation review, this remains outside `app/` unless a separate
Tool promotion review closes `PolicyEngine`, `ToolRegistry`, and runtime
contracts.

## Why Promotion Would Be Premature

Promoting this into a real Tool is PREMATURO until these decisions are closed:

- which parser dependency is allowed
- how malicious or malformed PDFs are handled
- max PDF size and page limits
- allowed input directories
- whether outputs may contain sensitive content
- how `created_at` should be defined for reproducibility
- whether parsing is read-only enough for current policy rules
- what `PolicyEngine` should authorize
- what error shape a Tool should return on parser failure
- what tests define the parser contract
- whether local LLM context files are allowed runtime inputs
- how `ToolRegistry` should represent parser capability and risk

Until then, keeping this lab external reduces drift risk in the production
contracts between `PolicyDecision`, `PolicyEngine`, `AgentRuntime`, and
`ToolRegistry`.
