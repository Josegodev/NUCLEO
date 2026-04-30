# RAG NUCLEO Docs

Deterministic lexical retrieval over live Markdown documentation in the NUCLEO
repository.

Este módulo no ejecuta herramientas ni interactúa con el runtime de NUCLEO.

## Purpose

This module helps inspect current Markdown documentation during HARDENING. It
builds a local lexical index from `.md` files and retrieves matching snippets
from those files.

It is not part of the NUCLEO runtime. It is not an agent. It does not execute
tools. It does not call `AgentService`, `AgentRuntime`, `Planner`,
`PolicyEngine`, `ToolRegistry`, or production `Tools`.

## Limits

- Read-only access to source Markdown files.
- Writes only to `runtime_lab/llm_lab/rag_nucleo_docs/.index/`.
- No imports from `app/`.
- No LLM usage.
- No embeddings.
- No vector database.
- No semantic similarity.
- No generated synthesis in the retrieval contract.
- No access to `CONTROL_OPERATIVO`.
- Excludes generated outputs, snapshots, deprecated docs, historical reports,
  external repositories, and this lab directory from retrieval.

If no documentary evidence is found, the answer is exactly:

```text
NO_CONSTA_EN_DOCUMENTACION
```

## Flow

```text
ingest_md.py
  -> discover allowed Markdown files
chunk_md.py
  -> split files by #, ##, ### headings
build_index.py
  -> tokenize chunks and write .index/md_chunks_index.json
search.py
  -> load index, normalize query, score chunks, rank, and return top_k results
query_index.py
  -> temporary legacy wrapper around search.py
```

## Public API

`search.py` is the only public API for deterministic retrieval:

```python
search(query: str, top_k: int = 5)
```

`query_index.py` is a temporary legacy wrapper. It must not contain scoring,
ranking, filtering, or result-building logic of its own.

This retrieval API returns evidence snippets only. It does not generate an
answer, call an LLM, use embeddings, or connect to a vector database.

## Scoring

Retrieval is still lexical only. It does not use embeddings or semantic
similarity. Scores combine token overlap with a document-type weight so that
contractual documentation is prioritized over examples:

- `docs/modules/code_contracts.md`
- `docs/modules/`
- `docs/architecture.md`
- `docs/operations/`
- `README.md`
- `docs/vision/`
- `docs/planning/`

For `dry_run` questions, chunks with exact non-execution phrases such as
`does not call tool.run` or `no llama a tool.run` receive a small lexical boost.

## CLI

Run from the repository root:

```bash
python3 -m runtime_lab.llm_lab.rag_nucleo_docs.build_index
python3 -m runtime_lab.llm_lab.rag_nucleo_docs.query_index "Qué hace dry_run=True?"
```

Do not run these files directly as loose scripts. They use package-relative
imports so that local modules such as `config.py` are resolved unambiguously.

## Output Contracts

`search.py` returns:

```json
{
  "query": "...",
  "question": "...",
  "status": "FOUND",
  "results": [
    {
      "doc_id": "...",
      "score": 1.0,
      "snippet": "...",
      "chunk_id": "...",
      "file": "...",
      "heading": "...",
      "start_line": 1,
      "end_line": 10,
      "text": "..."
    }
  ]
}
```

When no evidence is found:

```json
{
  "query": "...",
  "question": "...",
  "status": "NO_CONSTA_EN_DOCUMENTACION",
  "results": []
}
```

`eval_cases.json` is an optional JSON array of evaluation cases. An empty suite
is represented as `[]`.
