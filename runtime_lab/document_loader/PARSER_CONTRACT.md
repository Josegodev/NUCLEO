# Parser Contract

Classification: CRITICO

This contract defines the shape a future local PDF parser must satisfy before
it can write document records for NUCLEO HARDENING experiments.

The parser is not integrated yet. OpenDataLoader or any other parser remains
PREMATURO until this contract is implemented and tested.

Operational limits are defined in `loader_config.py`. Error shape and error
codes are defined in `ERROR_MODEL.md`.

## Parser Adapter Boundary

The loader must call a parser through the adapter contract, not through parser
library internals.

Current adapter:

- `NoOpPdfParser`
- returns `parser_status = "no parser integrated"`
- returns `records = []`
- returns a normalized `parser_unavailable` warning

Future parser adapters, including an OpenDataLoader adapter, must return a
`ParserResult` with:

- `parser_status`
- `records`
- `errors`

Adapter responsibilities:

- do not report partial silent success
- do not silently truncate content
- return normalized errors only
- return records that conform to `validate_jsonl_contract.py`
- keep parser-specific behavior behind the adapter
- never invent extracted content

An OpenDataLoader adapter may exist as a disabled stub. While disabled, it must
return a normalized `parser_disabled` warning and no records. If explicitly
enabled before real integration, it must return `parser_not_integrated` or raise
a controlled implementation error during development.

The loader must not import or depend on OpenDataLoader internals directly.
Real parsers must be adapter-based.

## Allowed Input

Allowed input is a local PDF file path only.

Rules:

- the input must be provided explicitly by the operator
- the path must resolve to a local file
- the file suffix must be `.pdf`
- directories, URLs, API payloads, remote storage paths, and network locations
  are not allowed

## Output Record Schema

Each JSONL line must be one JSON object with these required fields:

```json
{
  "document_id": "sha256-of-source-pdf",
  "source_path": "/absolute/path/to/source.pdf",
  "page": 1,
  "block_type": "text",
  "content": "real extracted content",
  "content_hash": "sha256-of-content",
  "created_at": "1970-01-01T00:00:00Z"
}
```

Required field types:

| Field | Type | Rule |
| --- | --- | --- |
| `document_id` | string | 64 lowercase hexadecimal characters |
| `source_path` | string | resolved local source path |
| `page` | integer | page number reported by the parser, starting at `1` |
| `block_type` | string | one of the allowed block types |
| `content` | string | real parser output only |
| `content_hash` | string | SHA256 hash of `content` encoded as UTF-8 |
| `created_at` | string | deterministic metadata timestamp for the run |

## Allowed Block Types

Allowed `block_type` values:

- `text`
- `table`
- `image`
- `metadata`

No other block types are allowed until the contract is updated.

## Deterministic document_id Rules

`document_id` must be:

```text
sha256(source_pdf_bytes)
```

The same PDF bytes must always produce the same `document_id`, regardless of
file name or file location.

The output path must use the full `document_id`:

```text
runtime_lab/knowledge_store/documents/<document_id>.jsonl
```

## Deterministic content_hash Rules

`content_hash` must be:

```text
sha256(content.encode("utf-8"))
```

The validator must reject a record when `content_hash` does not match
`content`.

## Error Model

The loader manifest must contain:

```json
{
  "parser_status": "no parser integrated",
  "errors": []
}
```

Current allowed `parser_status` values:

- `no parser integrated`
- `parsed`
- `parser_error`
- `input_error`

Rules:

- Empty JSONL is valid only when `parser_status` is `no parser integrated`.
- Parser failures must not write fake records.
- Parser failures must be represented in `errors`.
- Invalid records must make validation fail with a non-zero exit code.
- Silent truncation is forbidden. If content exceeds a configured limit, reject
  it with a normalized error instead of shortening it.

Future parser errors should use stable categories before Tool promotion. Current
placeholder categories:

- `invalid_input`
- `file_too_large`
- `too_many_pages`
- `malformed_pdf`
- `parser_exception`
- `empty_output`
- `parser_timeout`
- `parser_failed`
- `too_many_records`
- `content_record_too_large`
- `content_total_too_large`
- `page_limit_exceeded`

## Limits

Hardening defaults are defined in `loader_config.py`:

- max file size: `MAX_PDF_BYTES`
- max pages: `MAX_PAGES`
- parser timeout: `PARSER_TIMEOUT_SECONDS`
- max records per document: `MAX_RECORDS_PER_DOCUMENT`
- max content chars per record: `MAX_CONTENT_CHARS_PER_RECORD`
- max total content chars: `MAX_TOTAL_CONTENT_CHARS`
- allowed input roots: `ALLOWED_INPUT_ROOTS`
- default output root: `DEFAULT_OUTPUT_ROOT`

These are conservative placeholders. They must be reviewed before parser
integration and before any Tool promotion.

### Parser Timeout Behavior

A real parser must stop when execution exceeds `PARSER_TIMEOUT_SECONDS`.
Timeouts must produce a normalized `parser_timeout` error. Partial output must
not be treated as successful parsed content unless the contract is explicitly
changed.

### Max Records Behavior

If a parser produces more than `MAX_RECORDS_PER_DOCUMENT`, the document must be
rejected with `too_many_records`. Extra records must not be silently dropped.

### Max Content Length Behavior

If one record has `content` longer than `MAX_CONTENT_CHARS_PER_RECORD`, the
document must be rejected with `content_record_too_large`.

If the sum of all record `content` lengths exceeds `MAX_TOTAL_CONTENT_CHARS`,
the document must be rejected with `content_total_too_large`.

### Page Limit Behavior

If a parser detects more than `MAX_PAGES`, it must reject the document with
`page_limit_exceeded`.

### Parser Failure Semantics

Parser exceptions, invalid parser output, unsupported encrypted PDFs, malformed
PDFs, timeout, or limit violations must produce normalized errors and must not
write fake extraction records.

If an adapter returns records that fail `validate_jsonl_contract.py`, the loader
must reject the adapter output before writing JSONL or context Markdown.

## Security Notes

Malformed PDFs are security-relevant input. A parser must be treated as an
untrusted boundary because PDFs may contain unusual structures, compression
patterns, embedded files, malformed page trees, or payloads that trigger parser
bugs.

Before integration:

- choose a maintained parser dependency
- define timeout and memory limits
- enforce `MAX_PDF_BYTES` before reading the full PDF
- enforce record and content limits before context Markdown is trusted
- reject unsupported encrypted or remote inputs
- avoid executing embedded actions
- keep parsing outside `app/`
- keep generated content out of production authorization decisions

## Promotion Requirements Before Becoming A NUCLEO Tool

Promotion to `ToolRegistry` is PREMATURO until these are closed:

- parser dependency and version policy
- exact parser block schema
- max file size and max page count
- malformed PDF error behavior
- permission and role rules in `PolicyEngine`
- allowed source directories
- sensitive content handling
- deterministic test fixtures
- runtime error schema
- audit/tracing expectations

Until then, this contract belongs only to `runtime_lab/document_loader`.
