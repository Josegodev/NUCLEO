# Local LLM Context For Document Loader

Classification: INFORMATIVO

This document explains how `runtime_lab/document_loader` prepares plain local
context files for external local model runners.

## Pipeline

```text
PDF -> JSONL -> context.md
```

The intended full path is:

```text
PDF -> local parser -> normalized JSONL -> local LLM context Markdown
```

The current parser is not integrated yet. For now, the loader creates:

- `runtime_lab/knowledge_store/documents/<document_id>.jsonl`
- `runtime_lab/knowledge_store/manifests/<document_id>.manifest.json`
- `runtime_lab/knowledge_store/llm_context/<document_id>.context.md`

The JSONL file may be empty. Empty output means no parser has produced real
content yet.

## Consumers

The `.context.md` file is read-only input for local model experiments such as:

- Mistral local scripts
- Qwen local scripts
- Ollama prompt or context injection

Those consumers are external observers. They are not part of the NUCLEO runtime
pipeline.

This lab does not call Mistral, Qwen, Ollama, or any remote service. It only
writes plain files that those scripts may read later.

## Runtime Boundary

This is not RAG yet. RAG means retrieval-augmented generation: a system searches
stored content and injects selected pieces into a model prompt. This lab does
not implement retrieval, ranking, embeddings, indexing, or model calls.

This is not a NUCLEO Tool yet. It does not:

- subclass `BaseTool`
- register in `ToolRegistry`
- call `AgentRuntime`
- call `Planner`
- call `PolicyEngine`
- consume or produce `PolicyDecision`
- execute from `AgentService`

## Promotion Requirements

Promotion into `ToolRegistry` is PREMATURO until these contracts are closed:

- parser contract: exact block schema, page numbering, and supported formats
- policy contract: who may parse which paths and under what roles
- limits: max file size, max page count, timeout, and output size
- error schema: malformed PDF, parser failure, permission failure, empty output
- storage contract: retention, overwrite behavior, and sensitive data handling
- tests: deterministic fixtures for PDF -> JSONL -> context Markdown

