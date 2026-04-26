# llm-council Phase 01 Architecture Audit

## Summary

Scope inspected:

- `external/llm-council/README.md`
- `external/llm-council/pyproject.toml`
- `external/llm-council/backend/main.py`
- `external/llm-council/backend/council.py`
- `external/llm-council/backend/openrouter.py`
- `external/llm-council/backend/storage.py`
- `external/llm-council/backend/config.py`
- `external/llm-council/frontend/src/api.js`
- `external/llm-council/frontend/src/App.jsx`
- `external/llm-council/frontend/src/components/ChatInterface.jsx`
- `external/llm-council/frontend/src/components/Stage1.jsx`
- `external/llm-council/frontend/src/components/Stage2.jsx`
- `external/llm-council/frontend/src/components/Stage3.jsx`

No code was modified.

Audit boundary:

- This repository is useful only as an external reference for NUCLEO `llm_lab` experiment orchestration.
- It must not be treated as a NUCLEO core architecture reference.
- This audit does not propose using OpenRouter in NUCLEO.

Core finding:

`llm-council` implements a simple three-stage orchestration pattern:

1. fan out one user query to multiple models;
2. ask models to review/rank anonymized peer responses;
3. ask a chairman model to synthesize a final answer.

The implementation is intentionally lightweight. It uses FastAPI for boundaries, async `httpx` for provider calls, `asyncio.gather()` for fan-out, Server-Sent Events for progress updates, and JSON files for persistence.

The useful reference value for NUCLEO is the experiment flow shape, not the provider dependency or exact code quality.

## Backend Architecture

Backend entrypoint:

- `backend/main.py`

Framework:

- FastAPI
- Pydantic request/response models
- CORS enabled for local frontend origins
- Uvicorn server on port `8001` when run directly

Routes:

| Route | Method | Purpose |
|---|---:|---|
| `/` | `GET` | Health-style root endpoint |
| `/api/conversations` | `GET` | List conversation metadata |
| `/api/conversations` | `POST` | Create conversation |
| `/api/conversations/{conversation_id}` | `GET` | Fetch full conversation |
| `/api/conversations/{conversation_id}/message` | `POST` | Run full council and return all stages after completion |
| `/api/conversations/{conversation_id}/message/stream` | `POST` | Run council with Server-Sent Events per stage |

Boundary shape:

- Conversation creation is separate from message submission.
- Message submission validates conversation existence before orchestration.
- Non-streaming route returns a single combined response.
- Streaming route emits stage lifecycle events and saves the assistant message after all stages complete.

HTTP error behavior:

- Missing conversation returns `404`.
- Streaming route catches broad exceptions and emits an SSE event:

```json
{"type": "error", "message": "..."}
```

Error taxonomy is minimal. There is no typed orchestration error model in inspected files.

## Orchestration Flow

Main orchestration module:

- `backend/council.py`

Primary functions:

- `stage1_collect_responses(user_query)`
- `stage2_collect_rankings(user_query, stage1_results)`
- `stage3_synthesize_final(user_query, stage1_results, stage2_results)`
- `calculate_aggregate_rankings(stage2_results, label_to_model)`
- `generate_conversation_title(user_query)`
- `run_full_council(user_query)`

Non-streaming flow:

1. Add user message to storage.
2. If first message, generate title.
3. Run `run_full_council(...)`.
4. Store assistant message with `stage1`, `stage2`, and `stage3`.
5. Return all stages plus metadata.

Streaming flow:

1. Add user message to storage.
2. Start title generation in parallel if this is the first message.
3. Emit `stage1_start`.
4. Run Stage 1.
5. Emit `stage1_complete`.
6. Emit `stage2_start`.
7. Run Stage 2.
8. Calculate aggregate rankings.
9. Emit `stage2_complete` with metadata.
10. Emit `stage3_start`.
11. Run Stage 3.
12. Emit `stage3_complete`.
13. Await title generation and emit `title_complete`, if applicable.
14. Store assistant message.
15. Emit `complete`.

Useful pattern for `llm_lab`:

- Stage boundaries are explicit.
- Long-running orchestration is externally observable.
- Partial progress can be streamed without exposing token streaming.
- Final persistence happens after successful full-stage completion.

Limitation:

- If the streaming flow errors after adding the user message but before saving the assistant message, the conversation can retain only the user message. Recovery behavior is not implemented in inspected files.

## Async Fan-Out Pattern

Implementation:

- `backend/openrouter.py::query_models_parallel`

Pattern:

```python
tasks = [query_model(model, messages) for model in models]
responses = await asyncio.gather(*tasks)
return {model: response for model, response in zip(models, responses)}
```

Behavior:

- All model calls are launched concurrently.
- Results are returned as a dict keyed by model ID.
- `query_model(...)` catches all exceptions, logs to stdout, and returns `None`.
- Stage functions filter out failed model responses.

Timeout:

- `query_model(...)` default timeout is `120.0` seconds.
- Title generation uses `30.0` seconds.

Useful pattern:

- Fan-out can be represented as `model_id -> optional response`.
- Stage logic can proceed with partial successes.
- The caller does not fail the whole stage just because one model fails.

Hardening gap:

- `asyncio.gather()` is used without `return_exceptions=True`, but individual tasks catch exceptions internally.
- There is no per-stage minimum quorum except Stage 1's all-failed fallback.
- There is no concurrency limit.
- There is no cancellation policy once one stage becomes unrecoverable.
- Errors are collapsed to `None`, losing failure cause.

## Multi-Model Response Collection

Stage 1:

- Input: raw user query.
- Message sent to each model:

```json
[{"role": "user", "content": "<user query>"}]
```

Output shape:

```json
[
  {
    "model": "provider/model-id",
    "response": "model response text"
  }
]
```

Failure behavior:

- Failed model calls are omitted.
- If every model fails, `run_full_council(...)` returns:

```json
{
  "model": "error",
  "response": "All models failed to respond. Please try again."
}
```

Useful pattern:

- Preserve model attribution in lab data.
- Store raw individual responses before review/synthesis.
- Keep first-pass responses inspectable instead of only storing final synthesis.

Hardening gap:

- No schema validation on provider response beyond indexing `choices[0].message`.
- Missing or malformed provider body becomes `None` through broad exception handling.
- Token usage, latency, and error reason are not persisted.

## Peer Review and Ranking

Stage 2:

- Inputs:
  - original user query;
  - successful Stage 1 responses.

Anonymization:

- Stage 1 responses are labeled as `Response A`, `Response B`, etc.
- `label_to_model` preserves mapping:

```json
{
  "Response A": "provider/model-a",
  "Response B": "provider/model-b"
}
```

Review prompt:

- Each reviewing model receives the original question and all anonymized responses.
- The model is asked to evaluate each response and provide a final ranking in a strict text format.

Ranking parse:

- `parse_ranking_from_text(...)` searches for `FINAL RANKING:`.
- It extracts numbered entries matching `Response [A-Z]`.
- Fallback extracts any `Response [A-Z]` occurrences.

Stage 2 output shape:

```json
[
  {
    "model": "provider/reviewer-model",
    "ranking": "full review text",
    "parsed_ranking": ["Response C", "Response A", "Response B"]
  }
]
```

Aggregate ranking:

- `calculate_aggregate_rankings(...)` converts anonymous labels back to model IDs.
- It calculates average rank per model.
- Lower average rank is better.
- Output shape:

```json
[
  {
    "model": "provider/model-id",
    "average_rank": 1.67,
    "rankings_count": 3
  }
]
```

Useful pattern:

- Anonymize candidates before peer review.
- Keep raw reviews and parsed rankings.
- Store the label mapping as metadata.
- Aggregate ranking can be derived from reviews without being the only stored artifact.

Hardening gap:

- Ranking parser is regex-based and fragile.
- No validation confirms every response appears exactly once in each ranking.
- Self-review is not excluded. Each council model ranks the full anonymized set, including its own response, though model identity is hidden by labels.
- There is no weighting, quorum, tie handling, or confidence score.

## Final Synthesis

Stage 3:

- Implemented in `stage3_synthesize_final(...)`.
- Uses `CHAIRMAN_MODEL`.
- Prompt includes:
  - original question;
  - Stage 1 individual responses with model names;
  - Stage 2 peer rankings with reviewer model names;
  - instruction to synthesize a single final answer.

Output shape:

```json
{
  "model": "provider/chairman-model",
  "response": "final synthesized answer"
}
```

Failure behavior:

- If chairman call returns `None`, Stage 3 returns an error-like response with the chairman model ID:

```json
{
  "model": "provider/chairman-model",
  "response": "Error: Unable to generate final synthesis."
}
```

Useful pattern:

- Final synthesis is separated from peer scoring.
- The final answer has explicit provenance: model ID plus response text.
- Raw stages remain available for audit instead of only saving the final answer.

Hardening gap:

- Chairman receives non-anonymized model identities.
- The synthesis prompt is unstructured free text.
- There is no response schema for citations, dissent, confidence, or selected-source rationale.
- A failed chairman call is represented as a normal Stage 3 payload rather than a typed error.

## Persistence Format

Storage module:

- `backend/storage.py`

Storage location:

- `DATA_DIR = "data/conversations"`

File format:

- One JSON file per conversation:

```text
data/conversations/{conversation_id}.json
```

Conversation shape:

```json
{
  "id": "uuid",
  "created_at": "datetime iso string",
  "title": "New Conversation",
  "messages": []
}
```

User message shape:

```json
{
  "role": "user",
  "content": "question text"
}
```

Assistant message shape:

```json
{
  "role": "assistant",
  "stage1": [
    {"model": "provider/model", "response": "text"}
  ],
  "stage2": [
    {
      "model": "provider/model",
      "ranking": "text",
      "parsed_ranking": ["Response A"]
    }
  ],
  "stage3": {
    "model": "provider/model",
    "response": "text"
  }
}
```

Important inconsistency:

- The streaming API sends Stage 2 metadata to the frontend:

```json
{
  "label_to_model": {},
  "aggregate_rankings": []
}
```

- `storage.add_assistant_message(...)` persists only `stage1`, `stage2`, and `stage3`.
- It does not persist `metadata`.
- Therefore `label_to_model` and `aggregate_rankings` are available during streaming but are not saved in the conversation file in inspected code.

Useful pattern:

- JSON-per-conversation is easy to inspect for lab experiments.
- Persisting all stages supports later offline comparison.
- The staged assistant message shape is a good lab artifact pattern.

Hardening gap:

- File writes are synchronous.
- No file locking.
- No atomic write/rename.
- No schema version field.
- No metadata persistence for aggregate rankings.
- No stored latency, provider error, token count, timeout, or model config snapshot.
- Conversation ID is used directly in file path construction with no path-safety validation beyond generated UUID in normal create flow.

## FastAPI Boundaries

Observed API boundary:

- FastAPI owns conversation lifecycle and orchestration invocation.
- `backend/council.py` owns staged orchestration.
- `backend/openrouter.py` owns provider calls.
- `backend/storage.py` owns persistence.

Separation quality:

- The main module has a clear route-to-use-case mapping.
- Provider calls are isolated in one module.
- Storage is isolated in one module.
- Orchestration is separated from HTTP handlers.

Boundary weaknesses:

- HTTP handlers call storage directly before and after orchestration.
- There is no unit-of-work boundary around "add user message, run stages, add assistant message".
- Streaming errors do not roll back partial writes.
- Response models are defined for conversation reads but not for stage response payloads.
- No typed error envelope for orchestration failure.

SSE contract:

Event types:

- `stage1_start`
- `stage1_complete`
- `stage2_start`
- `stage2_complete`
- `stage3_start`
- `stage3_complete`
- `title_complete`
- `complete`
- `error`

Useful pattern:

- Stage-level SSE is enough for lab observability.
- The UI can update after each full stage without requiring token-level streaming.

Hardening gap:

- SSE parsing in frontend splits chunks by newline and assumes each `data:` line contains a full JSON object.
- Multi-line or chunk-split SSE payloads are not robustly buffered in inspected frontend code.

## Frontend Flow Notes

Frontend files inspected only to understand orchestration flow:

- `frontend/src/api.js`
- `frontend/src/App.jsx`
- `frontend/src/components/ChatInterface.jsx`
- `frontend/src/components/Stage1.jsx`
- `frontend/src/components/Stage2.jsx`
- `frontend/src/components/Stage3.jsx`

Flow:

- Frontend creates or selects a conversation.
- User sends one message.
- UI optimistically appends the user message and a partial assistant message.
- `sendMessageStream(...)` consumes SSE events.
- Stage completion events update the partial assistant message.
- Stage components render:
  - Stage 1 as per-model tabs;
  - Stage 2 as per-reviewer tabs plus aggregate ranking;
  - Stage 3 as final chairman answer.

Useful lab pattern:

- Progressive stage display makes multi-model orchestration explainable.
- Stage-by-stage rendering helps inspect disagreements before synthesis.

Ignored:

- Styling and visual layout were not audited except where needed to understand flow.

## Reusable Patterns for NUCLEO llm_lab

INFORMATIVE:

- Explicit three-stage experiment pipeline:
  - collect;
  - review/rank;
  - synthesize.
- Async fan-out using one task per model.
- Partial-success collection where failed model calls do not block successful responses.
- Stage-level progress events instead of token-level streaming.
- Anonymized peer review labels with a separate de-anonymization map.
- Preservation of raw individual responses and raw peer reviews.
- Aggregate ranking derived from parsed peer rankings.
- JSON-per-conversation persistence for inspectable lab artifacts.
- Separate modules for API, orchestration, provider client, and storage.

CRITICAL:

- Keep this pattern in `llm_lab` only, not NUCLEO core.
- Keep provider-specific APIs outside Runtime/Planner/PolicyEngine contracts.
- Do not treat OpenRouter as a NUCLEO dependency.
- Do not reuse broad exception-to-`None` handling for hardened backend contracts.
- Do not persist lab artifacts without schema versioning if they become long-lived.

PREMATURE:

- Porting this exact implementation.
- Using the ranking parser as a hardened evaluator.
- Using model self-review as an authoritative quality signal.
- Treating average rank as policy or safety judgment.
- Making this council flow part of normal Runtime execution.

## Non-Reusable or Forbidden Patterns

CRITICAL:

- Do not introduce OpenRouter into NUCLEO core.
- Do not let external model councils bypass NUCLEO PolicyEngine.
- Do not let peer ranking become a ToolRegistry or Runtime authorization signal.
- Do not collapse provider errors into `None` in hardened paths.
- Do not store only final synthesis when raw stages matter for audit.

INFORMATIVE:

- Regex parsing of model rankings is acceptable for a quick lab prototype but not a closed contract.
- JSON file persistence is useful for experiments but needs atomicity and schema versioning for hardening.
- SSE stage updates are useful, but client parsing should be robust if reused.

PREMATURE:

- Adding quorum, weighted voting, confidence scoring, or judge calibration before defining `llm_lab` experiment contracts.
- Building frontend polish before preserving stable experiment artifacts.

## Risks and Gaps

CRITICAL:

- External provider dependency is hard-coded through OpenRouter config.
- `OPENROUTER_API_KEY` is required for actual model calls.
- Provider failures are printed and converted to `None`, losing structured cause.
- No concurrency cap around fan-out.
- No durable state transition for in-progress or failed assistant messages.
- Stage 2 metadata is not persisted by `storage.add_assistant_message(...)`.

INFORMATIVE:

- The code is intentionally lightweight and local-development oriented.
- CORS is configured for local frontend ports.
- Title generation runs in parallel with Stage 1 in the streaming route.
- Conversation storage is human-readable.

PREMATURE:

- Treating this repository as production-grade orchestration.
- Using its persistence format as a durable NUCLEO event format without revision.
- Inferring safety or correctness from peer rankings alone.

## Recommendations for llm_lab Only

Recommended lab-only references:

- Use stage names and artifacts as an experiment vocabulary:
  - `stage1_responses`
  - `stage2_reviews`
  - `label_to_model`
  - `aggregate_rankings`
  - `stage3_synthesis`
- Store raw and parsed outputs together.
- Store stage metadata with the assistant artifact, not only in streaming events.
- Track model ID, latency, timeout, error type, and response length per call.
- Keep a schema version in persisted experiment files.
- Treat partial failures as first-class artifacts.
- Keep stage-level SSE as a useful observability pattern for long-running experiments.

Constraints:

- This belongs in `llm_lab` only.
- Do not use this as a NUCLEO Runtime, Planner, PolicyEngine, ToolRegistry, or AgentResponse design source.
- Do not propose or depend on OpenRouter for NUCLEO core.

## Open Questions

- What should the canonical `llm_lab` experiment artifact schema be?
- Should `llm_lab` store stage artifacts as JSONL events, conversation JSON, or both?
- Should model call failures be persisted as structured per-model records?
- Should peer review exclude a model from ranking its own response?
- Should aggregate ranking require every candidate to appear exactly once per reviewer?
- Should synthesis include dissent, confidence, and selected-source rationale as structured fields?
- Should stage-level SSE be standardized for `llm_lab` experiments?
