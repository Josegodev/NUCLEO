# Shimmy Phase 02 API Surface and Error Mapping

## Summary

Scope inspected:

- `runtime_lab/audit/shimmy_phase_01_entrypoints.md`
- `external/shimmy/src/server.rs`
- `external/shimmy/src/api.rs`
- `external/shimmy/src/openai_compat.rs`
- `external/shimmy/src/api_errors.rs`
- `external/shimmy/src/error.rs`
- `external/shimmy/src/model_registry.rs`, secondary scope, because `/v1/models` and `/v1/chat/completions` call registry methods directly.

No source code was modified.

Conclusion:

Shimmy's OpenAI-compatible non-streaming API is usable as a narrow future adapter boundary only if NUCLEO normalizes all error cases itself and sends `stream: false`.

`POST /v1/chat/completions` is the only generation route that should be considered for a future NUCLEO `LLMBackendAdapter`. It is not a fully stable error boundary because some failure paths return structured JSON and others return bare status responses.

`GET /v1/models` is acceptable for model listing. It has no explicit failure branch in the inspected handler.

`stream=true` is not safe for a hardened adapter because generation errors inside the streaming task are ignored and the handler still emits a final chunk and `[DONE]`.

## Routes Classified

Routes are registered in `src/server.rs::run`.

| Route | Handler | Classification | Justification |
|---|---|---:|---|
| `GET /health` | `health_check` | `allowed_for_future_adapter` | Returns basic service, version, model counts, and endpoint metadata. Safe for liveness/readiness probing. |
| `GET /metrics` | `metrics_endpoint` | `out_of_scope` | Observability endpoint. It shells out for GPU detection through helper functions. Not needed for inference contract validation. |
| `GET /diag` | `diag_handler` | `out_of_scope` | Diagnostic route from `util::diag`; not inspected because it is outside the requested core inference API. |
| `POST /api/generate` | `api::generate` | `explicitly_forbidden_for_NUCLEO` | Native Shimmy contract with different request/response/error shapes from OpenAI-compatible route. Using it would create a second inference contract. |
| `GET /api/models` | `api::list_models` | `explicitly_forbidden_for_NUCLEO` | Native Shimmy model-list shape differs from `/v1/models`; not needed if adapter uses OpenAI-compatible contract. |
| `POST /api/models/discover` | `api::discover_models` | `explicitly_forbidden_for_NUCLEO` | Discovery/mutation-adjacent operational surface. NUCLEO adapter should not control Shimmy discovery behavior. |
| `POST /api/models/:name/load` | `api::load_model` | `explicitly_forbidden_for_NUCLEO` | Placeholder load route returning `"status":"pending"`; not a verified model lifecycle contract. |
| `POST /api/models/:name/unload` | `api::unload_model` | `explicitly_forbidden_for_NUCLEO` | Placeholder unload route returning `"status":"pending"`; not a verified model lifecycle contract. |
| `GET /api/models/:name/status` | `api::model_status` | `explicitly_forbidden_for_NUCLEO` | Returns `"status":"unknown"` and `"loaded":false`; not a reliable readiness contract. |
| `GET /api/tools` | `api::list_tools` | `explicitly_forbidden_for_NUCLEO` | Tool surface must remain owned by NUCLEO `ToolRegistry` and `PolicyEngine`. |
| `POST /api/tools/:name/execute` | `api::execute_tool` | `explicitly_forbidden_for_NUCLEO` | Direct external tool execution would bypass NUCLEO policy and registry boundaries. |
| `POST /api/workflows/execute` | `api::execute_workflow` | `explicitly_forbidden_for_NUCLEO` | Workflow execution is outside inference backend responsibility and would overlap with NUCLEO Runtime/Planner ownership. |
| `GET /ws/generate` | `api::ws_generate` | `explicitly_forbidden_for_NUCLEO` | Separate WebSocket streaming protocol with different error behavior and response shape. |
| `POST /v1/chat/completions` | `openai_compat::chat_completions` | `allowed_for_future_adapter` | Narrowest OpenAI-like generation contract. Only acceptable with `stream:false` and adapter-side error normalization. |
| `GET /v1/models` | `openai_compat::models` | `allowed_for_future_adapter` | OpenAI-like model list route. IDs come from registry `list_all_available()`. |
| `POST /v1/messages` | `anthropic_compat::messages` | `explicitly_forbidden_for_NUCLEO` | Alternate Anthropic-compatible contract. Not inspected and not needed for a single OpenAI-compatible adapter boundary. |
| `POST /api/vision` | `api::vision`, feature-gated | `out_of_scope` | Feature-gated behind `vision`; explicitly ignored by audit scope. |

## /v1/chat/completions Contract

Source:

- `src/openai_compat.rs::ChatCompletionRequest`
- `src/openai_compat.rs::chat_completions`
- `src/api.rs::ChatMessage`

Request schema:

```rust
pub struct ChatCompletionRequest {
    pub model: String,
    pub messages: Vec<ChatMessage>,
    pub stream: Option<bool>,
    pub temperature: Option<f32>,
    pub max_tokens: Option<usize>,
    pub top_p: Option<f32>,
    pub stop: Option<StopTokens>,
}

pub struct ChatMessage {
    pub role: String,
    pub content: String,
}
```

Required fields:

- `model`: string.
- `messages`: array of objects with `role` string and `content` string.

Optional fields:

- `stream`: boolean.
- `temperature`: number parsed as `f32`.
- `max_tokens`: non-negative integer parsed as `usize`.
- `top_p`: number parsed as `f32`.
- `stop`: either string or array of strings.

Unsupported or ignored OpenAI fields:

- Any unknown request field is ignored by Serde because `deny_unknown_fields` is not present.
- Not present in request struct: `n`, `tools`, `tool_choice`, `function_call`, `functions`, `response_format`, `seed`, `logit_bias`, `logprobs`, `top_logprobs`, `presence_penalty`, `frequency_penalty`, `user`, `metadata`, `modalities`, `audio`, `prediction`, `service_tier`, and other OpenAI fields not listed above.
- No explicit unsupported-feature error is returned for these fields in inspected code.

Message-to-prompt conversion:

1. The handler converts all messages into `(role, content)` pairs.
2. It chooses a template family from `spec.template`:
   - `"chatml"` -> `TemplateFamily::ChatML`
   - `"llama3"` or `"llama-3"` -> `TemplateFamily::Llama3`
   - otherwise uses model-name heuristics:
     - names containing `qwen` or `chatglm` -> `ChatML`
     - names containing `llama` -> `Llama3`
     - fallback -> `OpenChat`
3. It first calls `loaded.format_prompt(&pairs)`.
4. If native prompt formatting is unavailable:
   - it finds the last message whose role is exactly `"user"`;
   - if a user message exists, it treats all messages except the final array element as history using `take(messages.len().saturating_sub(1))`;
   - it passes `last_user_message` separately into `fam.render(None, &history, last_user_message)`;
   - if no user message exists, it renders all pairs as history.

Important contract note:

The fallback prompt logic finds the last user message, but history drops the final message by array position, not by the position of the last user message. If the final message is not the last user message, prompt construction behavior may be surprising. No validation rejects such message order in inspected code.

`stream=true` behavior:

- Returns Server-Sent Events through `Sse`.
- Sends an initial chunk with assistant role and no content.
- For each generated token, sends a serialized `ChatCompletionChunk`.
- Sends a final chunk with `finish_reason: "stop"`.
- Sends `[DONE]`.
- Internal generation is called with `opts_clone.stream = false`; token streaming is performed through callback.
- Generation errors inside the spawned task are assigned to `_` and ignored.
- Serialization failures are converted into `"{}"` chunks.

Stop-token handling:

- Starts with `fam.stop_tokens()`.
- If user provided `stop`, the value is converted to `Vec<String>` and appended.
- The merged list is assigned to `opts.stop_tokens`.

Generation option handling:

- `temperature`, if present, directly overwrites `opts.temperature`.
- `top_p`, if present, directly overwrites `opts.top_p`.
- `max_tokens`, if present, directly overwrites `opts.max_tokens`.
- `stream`, if present, directly overwrites `opts.stream`.
- No range validation for these fields is present in inspected handler code.

Non-streaming success response:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "model-name",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "generated text"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

`usage` is placeholder data in inspected code. All three token counts are set to `0`.

## /v1/models Contract

Source:

- `src/openai_compat.rs::models`
- `src/openai_compat.rs::ModelsResponse`
- `src/openai_compat.rs::ListModel`
- `src/model_registry.rs::Registry::list_all_available`

Response shape:

```json
{
  "object": "list",
  "data": [
    {
      "id": "model-id",
      "object": "model",
      "created": 1234567890,
      "owned_by": "shimmy"
    }
  ]
}
```

Model ID source:

- The handler calls `state.registry.list_all_available()`.
- `list_all_available()` combines:
  - keys from manually registered models;
  - keys from `discovered_models`;
  - sorted and deduplicated strings.

Failure behavior:

- No explicit error branch is present in `openai_compat::models`.
- If no models are available, inspected code would return `"data":[]`.
- Handler-level failure is not verified in inspected files.

## Error Mapping Table

Failure paths for `POST /v1/chat/completions`.

| Failure path | Source file/function | Triggering condition | HTTP status | Body shape | Structured? | Recommended NUCLEO mapping | Retry safe? |
|---|---|---|---:|---|---|---|---|
| Invalid JSON body | `openai_compat::chat_completions` signature uses `Json<ChatCompletionRequest>`; Axum extractor handles rejection before function body | Request body is not valid JSON | Not verified in inspected files | Not verified in inspected files | Not verified | `invalid_request` | No |
| Missing required field | Same as above | Missing `model`, `messages`, `role`, or `content` during deserialization | Not verified in inspected files | Not verified in inspected files | Not verified | `invalid_request` | No |
| Wrong field type | Same as above | Example: `messages` not array, `temperature` not number, `max_tokens` negative or non-integer | Not verified in inspected files | Not verified in inspected files | Not verified | `invalid_request` | No |
| Unsupported OpenAI fields supplied | `ChatCompletionRequest` lacks fields and does not deny unknown fields | Request includes unsupported fields such as `tools`, `tool_choice`, `n`, `response_format`, etc. | `200` if rest of request succeeds | Normal success or later failure | No explicit error | Adapter should pre-reject as `unsupported_feature` if caller asks for unsupported behavior | No |
| Empty `messages` | `openai_compat::chat_completions` | `messages: []`; no validation rejects it | Depends on model load/generation | Normal success or later failure | No explicit error | Adapter should pre-reject as `invalid_request` | No |
| Invalid message role | `openai_compat::chat_completions` | Role is any string outside expected chat roles; no validation rejects it | Depends on model load/generation | Normal success or later failure | No explicit error | Adapter should pre-reject as `invalid_request` | No |
| Model not found | `openai_compat::chat_completions` | `state.registry.to_spec(&req.model)` returns `None` | `404` | `{ "error": { "message": "...", "type": "invalid_request_error", "param": "model", "code": "model_not_found" } }` | Yes | `model_not_found` | No |
| Model load failed | `openai_compat::chat_completions` | `engine.load(&spec).await` returns `Err` | `502` | Bare status response | No | `model_load_failed`; if adapter cannot distinguish from transport failure, use `backend_unavailable` only for connection-level failure | Yes, conditionally |
| Non-stream generation failed | `openai_compat::chat_completions` | `loaded.generate(&prompt, opts, None).await` returns `Err` and `stream` is false | `502` | Bare status response | No | `generation_failed` | Maybe, depending on idempotency and backend health |
| Stream generation failed | `openai_compat::chat_completions` | `loaded.generate(...).await` returns `Err` inside spawned task and `stream` is true | `200` SSE already established | Final chunk plus `[DONE]`; generation error is ignored | No reliable error body | `malformed_response` if adapter ever receives this; better pre-reject/disable streaming as `unsupported_feature` | No |
| Stream chunk serialization failed | `openai_compat::chat_completions` | `serde_json::to_string(...)` fails for chunk | `200` SSE | `"{}"` event data | Invalid OpenAI chunk | `malformed_response` | No |
| Timeout | No timeout code found in inspected files | Backend call exceeds NUCLEO client timeout | No Shimmy HTTP mapping verified | NUCLEO-side condition | N/A | `timeout` | Yes, with adapter policy |
| Malformed success body | Not produced by non-stream success path in inspected code, but possible over network/proxy/client parse | HTTP `200` with body not matching expected schema | `200` | Invalid JSON or invalid schema | No | `malformed_response` | Maybe |
| Unknown backend error | No catch-all JSON error envelope in inspected handler | Any unclassified non-2xx, connection close, or unexpected response | Varies | Varies | Varies | `unknown_backend_error` or `backend_unavailable` for connection-level failure | Maybe |

Notes:

- `src/api_errors.rs` defines `ApiError` and `ErrorResponse`, but `openai_compat::chat_completions` does not use that type in inspected code.
- `src/error.rs` defines `ShimmyError`, but the OpenAI-compatible HTTP handler maps errors manually.
- There is no verified Shimmy-side timeout mapping in inspected files.
- There is no verified request-level range validation for `temperature`, `top_p`, or `max_tokens` in inspected handler code.

## Response Validation Rules

For future NUCLEO adapter use, only validate non-streaming `/v1/chat/completions` responses.

Minimum valid success response:

- HTTP status must be `200`.
- Body must be valid JSON object.
- `object` must be string `"chat.completion"`.
- `id` must be a string.
- `created` must be a number.
- `model` must be a string.
- `choices` must be a non-empty array.
- `choices[0]` must be an object.
- `choices[0].message` must be an object.
- `choices[0].message.role` must be string `"assistant"`.
- `choices[0].message.content` must be a string.
- `choices[0].finish_reason`, if present, must be a string or null.

Fields to ignore:

- `usage.prompt_tokens`
- `usage.completion_tokens`
- `usage.total_tokens`

Reason:

The inspected non-streaming success path always sets usage counts to `0`; these values are not reliable for budget or policy accounting.

Invalid success cases to map to `malformed_response`:

- HTTP `200` with invalid JSON.
- HTTP `200` with no `choices`.
- HTTP `200` with empty `choices`.
- HTTP `200` with missing `choices[0].message.content`.
- HTTP `200` with non-string `choices[0].message.content`.
- HTTP `200` with `choices[0].message.role` not equal to `"assistant"`.
- HTTP `200` with streaming SSE when adapter requested non-streaming JSON.
- HTTP `200` stream event containing `{}` as a chunk.
- HTTP `200` stream ending with `[DONE]` but no content chunks, if adapter ever permits streaming.

Adapter-side request validation recommended before calling Shimmy:

- Require `stream == false`.
- Require exactly one selected model string.
- Require `messages` to be non-empty.
- Require each message role to be in the adapter-supported role set.
- Require each message content to be a string and non-null.
- Reject unsupported OpenAI features before sending the request.
- Validate numeric ranges for `temperature`, `top_p`, and `max_tokens` according to NUCLEO policy because Shimmy does not do so in inspected handler code.

## Explicitly Forbidden Surfaces for NUCLEO

The following routes must not be called by NUCLEO Runtime, Planner, PolicyEngine, ToolRegistry, or a future Shimmy LLM adapter:

- `POST /api/generate`
- `GET /api/models`
- `POST /api/models/discover`
- `POST /api/models/:name/load`
- `POST /api/models/:name/unload`
- `GET /api/models/:name/status`
- `GET /api/tools`
- `POST /api/tools/:name/execute`
- `POST /api/workflows/execute`
- `GET /ws/generate`
- `POST /v1/messages`

Reasons:

- They create alternate contracts.
- They overlap with NUCLEO-owned planner, policy, registry, tool, or workflow responsibilities.
- Some are placeholders or return non-authoritative state.
- Some have different error behavior from the OpenAI-compatible route.

## Adapter Boundary Recommendation

Allowed future adapter routes:

- `GET /health`
- `GET /v1/models`
- `POST /v1/chat/completions` with `stream:false` only

The adapter must normalize before returning to Runtime:

- Axum/request rejection or client-side bad request -> `invalid_request`
- 404 structured model error -> `model_not_found`
- 502 during load stage -> `model_load_failed`
- 502 during non-stream generation stage -> `generation_failed`
- Connection refused, DNS failure, TCP failure, process unavailable -> `backend_unavailable`
- Client-side timeout -> `timeout`
- HTTP 200 with invalid or incomplete success schema -> `malformed_response`
- Request requiring unsupported fields or streaming -> `unsupported_feature`
- Any other unclassified non-2xx or unexpected response -> `unknown_backend_error`

Boundary decision:

`/v1/chat/completions` is stable enough as a single non-streaming contract boundary only if NUCLEO treats Shimmy as an untrusted backend and validates both request and response at the adapter boundary.

It is not stable enough as a raw pass-through OpenAI API.

It is not stable enough with `stream:true` for HARDENING because stream generation failures are swallowed in inspected code.

## Open Questions for Phase 03

- Where should NUCLEO define its internal `LLMBackendAdapter` response and error contract?
- Does NUCLEO already have a backend error taxonomy matching the proposed names, or does it need a small closed enum?
- Should adapter-side validation reject unsupported OpenAI fields strictly, even though Shimmy ignores them?
- Should NUCLEO allow empty assistant content as valid output, or map it to `malformed_response` or `generation_failed`?
- What timeout budget should NUCLEO enforce for model listing, health checks, and generation?
- Should model IDs from `/v1/models` be treated as authoritative, or should NUCLEO require explicit model allowlisting?
- Should Phase 03 inspect the engine trait and load/generate implementation only enough to separate `model_load_failed` from `generation_failed` more precisely?
