# Parser Activation Checklist

Classification: CRITICO

This checklist must be completed before enabling any real PDF parser adapter,
including the disabled OpenDataLoader adapter stub.

Current status:

- `NoOpPdfParser` remains the default parser.
- `OpenDataLoaderPdfParser` exists only as a disabled stub.
- No real PDF content is parsed.
- No parser dependency is active.

## Required Gates

- [ ] dependency and version are pinned
- [ ] dependency license is reviewed
- [ ] parser has no network behavior
- [ ] parser timeout is enforceable
- [ ] max pages is enforceable
- [ ] max file size is enforced before parser execution
- [ ] malformed PDF behavior is tested
- [ ] partial output failure semantics are defined
- [ ] parser errors are mapped to `ERROR_MODEL.md`
- [ ] parser output passes `validate_jsonl_contract.py`
- [ ] fixtures use synthetic PDFs or explicitly approved PDFs only
- [ ] parser adapter has no `app/` imports
- [ ] no production `ToolRegistry` registration is added
- [ ] no `PolicyEngine` changes are added
- [ ] no LLM calls are added

## Activation Rule

Enabling a real parser is PREMATURO until every gate above is complete and
reviewed.

The loader must continue to depend on the adapter contract:

```text
BasePdfParser -> ParserResult -> validate_jsonl_contract.py -> JSONL/context
```

The loader must not depend on parser library internals.

