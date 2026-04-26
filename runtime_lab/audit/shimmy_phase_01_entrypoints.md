# Shimmy Phase 01 Entrypoints Audit

Scope: external inference backend candidate for NUCLEO.

Repository inspected: `external/shimmy`

Files inspected, by explicit scope only:

- `Cargo.toml`
- `src/main.rs`
- `src/lib.rs`
- `src/cli.rs`
- `src/server.rs`
- `src/api.rs`
- `src/openai_compat.rs`
- `src/api_errors.rs`
- `src/error.rs`

Files and areas intentionally ignored:

- `src/vision*`
- `cloudflare-worker/`
- `deploy/`
- `docs/`
- `tests/`
- `benches/`
- `scripts/`

## 1. Estado actual entendido

Shimmy is a Rust HTTP inference server with a CLI entrypoint and Axum routes.

For NUCLEO's architecture:

`Request -> FastAPI -> AgentService -> Runtime -> Planner -> PolicyEngine -> ToolRegistry -> Tool -> AgentResponse`

Shimmy should be evaluated only as a possible external inference backend behind the Runtime or AgentService boundary, not as a replacement for NUCLEO planner, policy, registry, or tool execution.

The relevant Shimmy inference entrypoints are:

- `POST /v1/chat/completions`
- `GET /v1/models`
- `POST /api/generate`
- `GET /api/models`
- `GET /health`
- `GET /metrics`
- `GET /ws/generate`

Shimmy also exposes non-core routes such as `/api/tools`, `/api/tools/:name/execute`, and `/api/workflows/execute`. These are out of scope for this audit because the request is limited to core inference server behavior.

## 2. Problema detectado

Classification: CRITICAL

The most important integration issue is that Shimmy has more than one inference contract and they are not identical.

There are two main HTTP generation paths:

- Native Shimmy path: `POST /api/generate`
- OpenAI-compatible path: `POST /v1/chat/completions`

They differ in request shape, response shape, streaming format, prompt construction, stop-token handling, and error response format.

Affected files:

- `src/server.rs`
- `src/api.rs`
- `src/openai_compat.rs`
- `src/api_errors.rs`
- `src/error.rs`

Minimum reasonable conclusion:

NUCLEO should choose one Shimmy HTTP contract as the integration boundary. The safest first candidate is `/v1/chat/completions`, because it is closer to a standard inference backend contract and avoids Shimmy-specific response shapes.

## 3. Impacto técnico

If NUCLEO integrates Shimmy without choosing a single contract, the Runtime may need conditional parsing for multiple response formats.

That creates contract drift. Contract drift means two parts of the system slowly stop agreeing about the same concept. Here, "a generation result" can mean either:

- `{ "response": "..." }` from `/api/generate`
- OpenAI-like `{ "choices": [...] }` from `/v1/chat/completions`

This also affects error handling.

Observed examples:

- `/api/generate` returns bare HTTP status codes for model-not-found and generation/load failure.
- `/v1/chat/completions` returns a structured JSON error for model-not-found, but bare `502 Bad Gateway` for load/generation failure.
- `src/api_errors.rs` defines an `ApiError` type, but the inspected inference handlers do not consistently use it.
- `src/error.rs` defines a broader `ShimmyError`, but the HTTP boundary mostly maps errors manually.

For NUCLEO hardening, this matters because Runtime needs deterministic backend outcomes:

- success
- invalid request
- model not found
- backend unavailable or load failed
- generation failed
- malformed backend response

Shimmy currently exposes some of those states, but not through one stable, uniform HTTP envelope.

## 4. Cambio mínimo recomendado

No code change is recommended in Shimmy during this phase.

Minimum recommended NUCLEO-side decision:

Use only:

- `GET /health` for liveness/readiness probing
- `GET /v1/models` for model listing
- `POST /v1/chat/completions` for inference

Do not use, in the first integration pass:

- `/api/generate`
- `/ws/generate`
- `/api/tools`
- `/api/workflows/execute`
- `/api/models/:name/load`
- `/api/models/:name/unload`

Reason:

This keeps Shimmy as an inference backend only. NUCLEO should keep ownership of Planner, PolicyEngine, ToolRegistry, and Tool execution.

## 5. Explicación pedagógica

Think of a contract as a plug shape.

If NUCLEO expects every inference backend to return an OpenAI-like response, then Shimmy's `/v1/chat/completions` plug mostly fits.

If NUCLEO also accepts `/api/generate`, then NUCLEO must understand a second plug shape. That is not impossible, but it increases entropy. Entropy here means the number of special cases the system must remember.

In HARDENING, the goal is not to support every possible path. The goal is to reduce ambiguity.

So the next important step is not to add features. It is to say:

"For Shimmy, NUCLEO talks only to the OpenAI-compatible inference endpoint."

This protects these NUCLEO boundaries:

- Runtime: receives one normalized backend response shape.
- Planner: remains independent from backend-specific prompt formatting.
- PolicyEngine: is not bypassed by Shimmy's tool/workflow endpoints.
- ToolRegistry: remains the only tool execution authority inside NUCLEO.

## 6. Pasos exactos para hacerlo

This audit did not modify Shimmy code.

The exact observed entrypoints are registered in `src/server.rs`:

- `GET /health`
- `GET /metrics`
- `GET /diag`
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
- `POST /v1/chat/completions`
- `GET /v1/models`
- `POST /v1/messages`

Recommended NUCLEO adapter contract:

1. Probe Shimmy with `GET /health`.
2. List models with `GET /v1/models`.
3. Send inference requests to `POST /v1/chat/completions`.
4. Reject or ignore Shimmy tool/workflow endpoints at the NUCLEO integration layer.
5. Normalize Shimmy failures into NUCLEO's own backend error types.

Recommended request shape for the first integration pass:

```json
{
  "model": "selected-model-name",
  "messages": [
    {
      "role": "user",
      "content": "prompt text"
    }
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 512,
  "top_p": 0.9
}
```

Expected success response shape from `/v1/chat/completions`:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "selected-model-name",
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

Important limitation:

The `usage` values are always zero in the inspected code path, so NUCLEO should not treat Shimmy token usage as authoritative.

## 7. Cómo comprobar si ha quedado bien

Manual validation commands, from `external/shimmy`, if Shimmy is running:

```bash
curl -s http://127.0.0.1:11435/health
```

Expected kind of result:

```json
{
  "status": "ok",
  "service": "shimmy",
  "version": "...",
  "models": {
    "total": 1,
    "discovered": 0,
    "manual": 1
  }
}
```

Model listing:

```bash
curl -s http://127.0.0.1:11435/v1/models
```

Expected kind of result:

```json
{
  "object": "list",
  "data": [
    {
      "id": "model-name",
      "object": "model",
      "created": 1234567890,
      "owned_by": "shimmy"
    }
  ]
}
```

Inference:

```bash
curl -s http://127.0.0.1:11435/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"model-name","messages":[{"role":"user","content":"Say hello"}],"stream":false,"max_tokens":32}'
```

Expected kind of result:

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "..."
      }
    }
  ]
}
```

Validation rule for NUCLEO:

Only accept a Shimmy inference response if:

- HTTP status is `200`.
- JSON has `choices`.
- `choices[0].message.content` exists and is a string.
- `usage` is optional or ignored.

## 8. Riesgos o dudas pendientes

CRITICAL: Error envelopes are inconsistent.

- `/v1/chat/completions` model-not-found returns structured JSON.
- `/v1/chat/completions` load/generation failure returns bare `502`.
- `/api/generate` returns bare status codes for important failures.
- `api_errors.rs` exists but is not consistently used by the inference handlers.

CRITICAL: Shimmy exposes tool and workflow routes.

This is not a problem if NUCLEO ignores them. It becomes a problem if a future integration accidentally lets Shimmy execute tools outside NUCLEO's PolicyEngine and ToolRegistry.

INFORMATIVO: `/v1/chat/completions` usage accounting is placeholder data.

The inspected code returns zero for prompt, completion, and total tokens. NUCLEO should not use Shimmy `usage` for billing, policy limits, or deterministic budget accounting.

INFORMATIVO: `GET /metrics` performs GPU detection by shelling out to system commands.

This is outside core inference response handling, but it means `/metrics` may have environment-dependent behavior. Use `/health` as the first simple probe.

INFORMATIVO: Startup has model availability checks.

The `serve` command exits if no models are available. That is useful for fail-fast behavior, but NUCLEO should still treat connection failure as backend unavailable.

PREMATURO: Changing Shimmy's error model.

It may be useful later, but this phase should not modify Shimmy. The smaller hardening move is to normalize errors in the NUCLEO adapter.

Next recommended change:

Define a NUCLEO-side Shimmy adapter contract that accepts only `/v1/chat/completions` and maps Shimmy responses into one internal `AgentResponse` or backend error shape.
