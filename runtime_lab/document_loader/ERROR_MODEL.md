# Error Model

Classification: CRITICO

This model defines normalized loader errors before any real PDF parser is
integrated.

## Error Shape

Each error object must contain:

```json
{
  "code": "non_pdf_input",
  "message": "input path must have a .pdf suffix",
  "severity": "error",
  "recoverable": true,
  "source": "input_validation"
}
```

Field meanings:

- `code`: stable machine-readable identifier.
- `message`: human-readable explanation.
- `severity`: `error` or `warning`.
- `recoverable`: whether the operator can retry with different input.
- `source`: component that produced the error.

Allowed `source` values for the current lab:

- `input_validation`
- `parser`
- `manifest`

## Current Error Codes

### invalid_path

Used when the provided path does not exist or is not a file.

```json
{
  "code": "invalid_path",
  "message": "input PDF does not exist: /tmp/missing.pdf",
  "severity": "error",
  "recoverable": true,
  "source": "input_validation"
}
```

### non_pdf_input

Used when the path exists but does not end in `.pdf`.

```json
{
  "code": "non_pdf_input",
  "message": "input path must have a .pdf suffix: /tmp/test.txt",
  "severity": "error",
  "recoverable": true,
  "source": "input_validation"
}
```

### file_too_large

Used when the input file is larger than `MAX_PDF_BYTES`.

```json
{
  "code": "file_too_large",
  "message": "input PDF exceeds MAX_PDF_BYTES: 5242881 > 5242880",
  "severity": "error",
  "recoverable": true,
  "source": "input_validation"
}
```

### path_outside_allowed_roots

Used when `ALLOWED_INPUT_ROOTS` is configured and the resolved input path is
outside those roots.

```json
{
  "code": "path_outside_allowed_roots",
  "message": "input path is outside configured ALLOWED_INPUT_ROOTS: /home/user/file.pdf",
  "severity": "error",
  "recoverable": true,
  "source": "input_validation"
}
```

### parser_unavailable

Used while no real PDF parser is integrated.

```json
{
  "code": "parser_unavailable",
  "message": "no PDF parser is integrated; no extraction was attempted",
  "severity": "warning",
  "recoverable": true,
  "source": "parser"
}
```

### parser_disabled

Used when a parser adapter exists but is explicitly disabled.

```json
{
  "code": "parser_disabled",
  "message": "OpenDataLoader adapter is declared but disabled",
  "severity": "warning",
  "recoverable": true,
  "source": "parser"
}
```

### parser_not_integrated

Used when a parser adapter is enabled before its implementation is reviewed and
integrated.

```json
{
  "code": "parser_not_integrated",
  "message": "OpenDataLoader adapter was enabled, but no parser implementation is integrated",
  "severity": "error",
  "recoverable": true,
  "source": "parser"
}
```

### parser_timeout

Used when parsing exceeds `PARSER_TIMEOUT_SECONDS`.

```json
{
  "code": "parser_timeout",
  "message": "parser exceeded PARSER_TIMEOUT_SECONDS: 11 > 10",
  "severity": "error",
  "recoverable": true,
  "source": "parser"
}
```

### parser_failed

Used when the parser raises an exception or returns structurally invalid output.

```json
{
  "code": "parser_failed",
  "message": "parser failed before producing valid records",
  "severity": "error",
  "recoverable": true,
  "source": "parser"
}
```

### too_many_records

Used when parser output exceeds `MAX_RECORDS_PER_DOCUMENT`.

```json
{
  "code": "too_many_records",
  "message": "record count exceeds MAX_RECORDS_PER_DOCUMENT: 1001 > 1000",
  "severity": "error",
  "recoverable": true,
  "source": "parser"
}
```

### content_record_too_large

Used when one record exceeds `MAX_CONTENT_CHARS_PER_RECORD`.

```json
{
  "code": "content_record_too_large",
  "message": "content length exceeds MAX_CONTENT_CHARS_PER_RECORD: 257 > 256",
  "severity": "error",
  "recoverable": true,
  "source": "parser"
}
```

### content_total_too_large

Used when total extracted content exceeds `MAX_TOTAL_CONTENT_CHARS`.

```json
{
  "code": "content_total_too_large",
  "message": "total content length exceeds MAX_TOTAL_CONTENT_CHARS: 100001 > 100000",
  "severity": "error",
  "recoverable": true,
  "source": "parser"
}
```

### page_limit_exceeded

Used when the parser detects more pages than `MAX_PAGES`.

```json
{
  "code": "page_limit_exceeded",
  "message": "page count exceeds MAX_PAGES: 101 > 100",
  "severity": "error",
  "recoverable": true,
  "source": "parser"
}
```

## Manifest Behavior

Input validation failures are rejected with a non-zero exit code and a
deterministic error manifest under:

```text
runtime_lab/knowledge_store/manifests/input-error-<hash>.manifest.json
```

The loader must not create fake JSONL records for failures.

Parser output must not be silently truncated. Limit violations are errors, not
successful partial extraction.
