# document_loader

Local document ingestion lab for HARDENING experiments.

This directory is external observer infrastructure only. It is not part of the
NUCLEO production execution path and it must not be imported by `app/`.

## Intended Pipeline

```text
PDF -> local parser -> normalized JSONL -> local LLM context
```

Current status:

- accepts a local PDF path
- validates that the input is a file with a `.pdf` suffix
- rejects paths outside configured lab input roots
- rejects files larger than `MAX_PDF_BYTES`
- computes a deterministic `document_id` from the PDF bytes
- writes to deterministic paths under `runtime_lab/knowledge_store/`
- creates a manifest JSON file for auditability
- creates a context Markdown file for local LLM readers
- does not extract text yet
- does not call an LLM
- does not fake extraction results

Because no parser is wired yet, the current scaffold writes an empty JSONL file.
That is intentional: empty output is safer than invented content.

## Output Layout

Generated files use this layout:

```text
runtime_lab/knowledge_store/
  documents/
    <document_id>.jsonl
  manifests/
    <document_id>.manifest.json
  llm_context/
    <document_id>.context.md
```

`document_id` is the SHA256 hash of the source PDF bytes. That keeps output
paths stable for the same PDF content.

## Runtime Boundary

This lab is outside the canonical NUCLEO runtime flow:

```text
Request -> FastAPI -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> Tool -> AgentResponse
```

This lab must not:

- import `app.runtime`
- call `AgentRuntime`
- act as `Planner`
- call `PolicyEngine`
- register anything in `ToolRegistry`
- execute production `Tools`
- change `PolicyDecision`

It may:

- read a local PDF explicitly provided by the operator
- write generated JSONL records inside this lab area
- prepare local context files for external LLM experiments

## JSONL Record Contract

When a real local parser is added, each emitted JSONL line must contain these
fields:

```json
{
  "document_id": "sha256-of-source-pdf",
  "source_path": "/absolute/path/to/source.pdf",
  "page": 1,
  "block_type": "text",
  "content": "real extracted content",
  "content_hash": "sha256-of-content",
  "created_at": "2026-04-26T00:00:00Z"
}
```

Field meanings:

- `document_id`: stable hash of the source PDF bytes.
- `source_path`: resolved local path used for this lab run.
- `page`: page number reported by the parser.
- `block_type`: parser block category, for example `text` or `table`.
- `content`: real parser output only. Placeholder text is not allowed.
- `content_hash`: stable hash of `content`.
- `created_at`: UTC timestamp for the normalization run.

The detailed parser contract is defined in `PARSER_CONTRACT.md`. That contract
is the source of truth for allowed input, required fields, allowed block types,
hash rules, parser errors, size/page placeholders, and Tool promotion gates.

Operational limits are defined in `loader_config.py`:

- `MAX_PDF_BYTES`
- `MAX_PAGES`
- `PARSER_TIMEOUT_SECONDS`
- `MAX_RECORDS_PER_DOCUMENT`
- `MAX_CONTENT_CHARS_PER_RECORD`
- `MAX_TOTAL_CONTENT_CHARS`
- `ALLOWED_INPUT_ROOTS`
- `DEFAULT_OUTPUT_ROOT`
- `PARSER_STATUS_NO_PARSER`

Normalized errors are defined in `ERROR_MODEL.md`.

## Parser Adapter

The loader depends on a parser adapter contract, not on parser library
internals.

Current parser:

- `NoOpPdfParser`
- emits no records
- returns `parser_status: no parser integrated`
- returns a normalized `parser_unavailable` warning

Declared but disabled parser:

- `OpenDataLoaderPdfParser`
- does not load the OpenDataLoader package
- defaults to `enabled=False`
- returns `parser_disabled` when called while disabled

Future parser:

- OpenDataLoader may be added only behind an adapter
- the loader should keep using `ParserResult`
- parser-specific behavior must not leak into the loader contract

The loader validates adapter output before writing JSONL or context Markdown.
Command behavior is unchanged: `load_pdf_to_jsonl.py` still uses
`NoOpPdfParser` by default.

Before enabling any real parser adapter, complete
`PARSER_ACTIVATION_CHECKLIST.md`.

Validate a generated JSONL file with:

```bash
python3 runtime_lab/document_loader/validate_jsonl_contract.py runtime_lab/knowledge_store/documents/<document_id>.jsonl
```

Validate deterministic fixtures:

```bash
python3 runtime_lab/document_loader/validate_jsonl_contract.py runtime_lab/document_loader/fixtures/valid_empty.jsonl
python3 runtime_lab/document_loader/validate_jsonl_contract.py runtime_lab/document_loader/fixtures/invalid_block_type.jsonl
```

The first command should pass. The second command should fail.

## Usage

From the repository root:

```bash
python3 runtime_lab/document_loader/load_pdf_to_jsonl.py path/to/document.pdf
```

Example output:

```text
source_pdf: /absolute/path/to/document.pdf
document_id: <sha256>
output_jsonl: /home/.../NUCLEO/runtime_lab/knowledge_store/documents/<document_id>.jsonl
output_manifest: /home/.../NUCLEO/runtime_lab/knowledge_store/manifests/<document_id>.manifest.json
output_context_md: /home/.../NUCLEO/runtime_lab/knowledge_store/llm_context/<document_id>.context.md
records_written: 0
parser_status: no parser integrated
```

Generated `.jsonl` files are already covered by the repository `.gitignore`
rule for `*.jsonl`. Generated manifest and context files under
`runtime_lab/knowledge_store/` are also ignored.

## Build Context From JSONL

The context builder reads JSONL and writes Markdown for local model scripts.
It does not call Mistral, Qwen, Ollama, or any API.

```bash
python3 runtime_lab/document_loader/build_llm_context.py runtime_lab/knowledge_store/documents/<document_id>.jsonl
```

## Smoke Test

Create a temporary PDF-shaped file:

```bash
printf '%s\n' '%PDF-1.4' > /tmp/test.pdf
```

Run the loader:

```bash
python3 runtime_lab/document_loader/load_pdf_to_jsonl.py /tmp/test.pdf
```

Then rebuild context from the generated JSONL:

```bash
python3 runtime_lab/document_loader/build_llm_context.py runtime_lab/knowledge_store/documents/<document_id>.jsonl
```

Validate the JSONL contract:

```bash
python3 runtime_lab/document_loader/validate_jsonl_contract.py runtime_lab/knowledge_store/documents/<document_id>.jsonl
```

Replace `<document_id>` with the value printed by the loader.

Expected result:

- JSONL file exists and may be empty while no parser is integrated.
- manifest JSON exists.
- context Markdown exists.
- `records_written` is `0`.
- `parser_status` is `no parser integrated`.
- JSONL validation passes because empty output is valid only in this parser
  placeholder state.

## Batch Smoke Test

Run the loader against every `*.pdf` file in a local folder:

```bash
python3 runtime_lab/document_loader/batch_smoke_test.py /path/to/local/pdf_folder
```

The batch runner delegates each PDF to `load_pdf_to_jsonl.py`. It does not parse
PDF content itself, does not call LLMs, and writes generated outputs under
`runtime_lab/knowledge_store/` by default.

Real PDFs used for this command are operational smoke inputs. They are not
contract fixtures and should not be committed.

## Unit Tests

This lab uses standard-library `unittest` tests because `pytest` is not required
by the current repository environment.

```bash
python3 -m unittest discover -s runtime_lab/document_loader/tests
```

The tests use synthetic JSONL fixtures and temporary files only. They do not use
real local PDFs, call LLMs, or integrate a parser.

## Failure Smoke Tests

Missing file:

```bash
python3 runtime_lab/document_loader/load_pdf_to_jsonl.py /tmp/nucleo_missing.pdf
```

Expected result:

- exit code is non-zero
- no JSONL records are created
- a deterministic rejection manifest is written
- `error_code` is `invalid_path`

Non-PDF file:

```bash
printf '%s\n' 'not a pdf' > /tmp/not_pdf.txt
python3 runtime_lab/document_loader/load_pdf_to_jsonl.py /tmp/not_pdf.txt
```

Expected result:

- exit code is non-zero
- no JSONL records are created
- a deterministic rejection manifest is written
- `error_code` is `non_pdf_input`

Oversized PDF-shaped file:

```bash
truncate -s 5242881 /tmp/oversized.pdf
python3 runtime_lab/document_loader/load_pdf_to_jsonl.py /tmp/oversized.pdf
```

Expected result:

- exit code is non-zero
- no JSONL records are created
- a deterministic rejection manifest is written
- `error_code` is `file_too_large`

This uses `5242881` bytes because the current hardening default is
`MAX_PDF_BYTES = 5242880`.

## OpenDataLoader Placeholder

OpenDataLoader-style integration belongs here only as a local parser adapter.
It must return real parser blocks before this scaffold writes records.

Acceptable future shape:

```text
PDF path -> OpenDataLoader/local parser adapter -> ParsedBlock list -> JSONL
```

Not acceptable:

```text
PDF path -> NUCLEO ToolRegistry -> Tool execution
```

See `LLM_CONTEXT.md` for the local LLM context boundary.
