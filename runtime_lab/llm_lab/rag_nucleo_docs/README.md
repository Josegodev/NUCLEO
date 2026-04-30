# RAG NUCLEO Docs

Experimental lexical retrieval over live Markdown documentation in the NUCLEO
repository.

Este módulo no ejecuta herramientas ni interactúa con el runtime de NUCLEO.

## Purpose

This module helps inspect current Markdown documentation during HARDENING. It
builds a local lexical index from `.md` files and answers questions by returning
extractive snippets from those files.

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
- No generated synthesis.
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
query_index.py
  -> score chunks by lexical token overlap weighted by document type
rag_answer.py
  -> concatenate retrieved snippets with file:line references
```

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
python3 -m runtime_lab.llm_lab.rag_nucleo_docs.rag_answer "Qué hace dry_run=True?"
python3 -m runtime_lab.llm_lab.rag_nucleo_docs.rag_answer "Qué hace dry_run=True?" --mode llm
```

Do not run these files directly as loose scripts. They use package-relative
imports so that local modules such as `config.py` are resolved unambiguously.

`rag_answer.py` supports:

- `--mode extractive` (default): returns retrieved snippets directly.
- `--mode llm`: calls `runtime_lab/llm_lab/model_adapter.py` with the retrieved
  chunks as bounded context. If retrieval finds no evidence, it does not call
  the model and returns `NO_CONSTA_EN_DOCUMENTACION`.


## Output Contracts

`query_index.py` returns:

```json
{
  "question": "...",
  "status": "FOUND",
  "results": [
    {
      "score": 1.0,
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

`rag_answer.py` returns extractive snippets:

```json
{
  "question": "...",
  "answer": "[docs/file.md:10] ...",
  "sources": [
    {
      "file": "docs/file.md",
      "heading": "Heading",
      "start_line": 10,
      "end_line": 20,
      "score": 0.5
    }
  ],
  "warnings": ["Extractive lexical retrieval only. No LLM synthesis or inference was used."]
}
```

When no evidence is found:

```json
{
  "answer": "NO_CONSTA_EN_DOCUMENTACION"
}
```
