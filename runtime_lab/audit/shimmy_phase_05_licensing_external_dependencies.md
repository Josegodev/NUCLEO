# Shimmy Phase 05 Licensing and External Dependency Audit

## Summary

Scope inspected:

- `runtime_lab/audit/shimmy_phase_01_entrypoints.md`
- `runtime_lab/audit/shimmy_phase_02_api_error_mapping.md`
- `runtime_lab/audit/shimmy_phase_03_model_runtime_resources.md`
- `runtime_lab/audit/shimmy_phase_04_engine_concurrency_memory.md`
- `external/shimmy/Cargo.toml`
- `external/shimmy/src/lib.rs`
- `external/shimmy/src/server.rs`
- `external/shimmy/src/api.rs`, only vision/licensing sections
- `external/shimmy/src/vision.rs`
- `external/shimmy/src/vision_adapter.rs`
- `external/shimmy/src/vision_license.rs`
- `external/shimmy/src/engine/adapter.rs`, only feature/backend selection
- `external/shimmy/src/engine/huggingface.rs`, only external process / model loading behavior
- `external/shimmy/src/engine/llama.rs`, only environment and GPU feature behavior
- `external/shimmy/src/metrics.rs`, only outbound telemetry and environment behavior
- `external/shimmy/src/auto_discovery.rs`, only environment behavior
- `external/shimmy/src/discovery.rs`, only environment behavior
- `external/shimmy/src/port_manager.rs`, only bind environment behavior
- `external/shimmy/cloudflare-worker/README.md`
- `external/shimmy/cloudflare-worker/stripe-keygen-webhook.js`
- `external/shimmy/cloudflare-worker/wrangler.toml`

No source code was modified.

Core finding:

Text inference through `POST /v1/chat/completions` is not directly coupled to Shimmy's Keygen, Stripe, or vision license checks in inspected files.

Licensing is implemented for the feature-gated vision path. The active HTTP route using it is `POST /api/vision`, registered only when the `vision` Cargo feature is enabled. The OpenAI-compatible text route does not call `VisionLicenseManager`, does not read `SHIMMY_LICENSE_KEY`, and does not call Keygen in inspected files.

However, Shimmy is not automatically an offline-only process:

- The `vision` feature can call Keygen and Hugging Face URLs.
- The Cloudflare worker calls Stripe and Keygen, but it is a separate deployment artifact.
- The optional telemetry module can POST to `https://metrics.shimmy-ai.dev/v1/usage`, although no production call site was found in inspected server/main files.
- The default `huggingface` feature can invoke Python `transformers.from_pretrained(...)`, which may perform external model downloads depending on local cache and Transformers configuration. This is not a Rust `reqwest` call, but it is an external dependency risk in the text backend selection path.

Final classification: **risky / requires isolation** unless the runtime is constrained to local GGUF llama text inference with vision, telemetry, and HuggingFace backend behavior disabled or isolated.

## Licensing System

Implementation location:

- `src/vision_license.rs`

License manager:

- `VisionLicenseManager`
- compiled only under `#[cfg(feature = "vision")]`
- stored in `AppState` as `vision_license_manager: Option<VisionLicenseManager>` only under the same feature gate

License validation path:

1. `api.rs::vision` receives `VisionRequest`.
2. If request license is missing, it reads `SHIMMY_LICENSE_KEY`.
3. It selects `SHIMMY_VISION_MODEL` or defaults to `minicpm-v`.
4. It requires `state.vision_license_manager`.
5. It calls `vision::process_vision_request(...)`.
6. `process_vision_request(...)` calls `license_manager.check_vision_access(...)` before image loading or inference.
7. `check_vision_access(...)` calls `validate_license(...)`.
8. `validate_license(...)` checks an in-memory/disk cache first.
9. On cache miss or expired cache, it calls `call_keygen_validate(...)`.

Local or remote:

- Cached validation is local.
- Cache files are stored under a user data directory: `shimmy/vision/license_cache.json` and `shimmy/vision/usage_stats.json`.
- Fresh validation is remote through Keygen.

External service:

- `call_keygen_validate(...)` sends `POST` to:
  - `https://api.keygen.sh/v1/accounts/{KEYGEN_ACCOUNT_ID}/licenses/actions/validate-key`
- `KEYGEN_ACCOUNT_ID` and `KEYGEN_PUBLIC_KEY` are hard-coded constants.
- Authorization token comes from `KEYGEN_API_KEY` or `KEYGEN_PRODUCT_TOKEN`.

Synchronous or cached:

- Validation is async.
- Cache is used before remote validation.
- Cache validity:
  - if license has `expires_at`, cache is accepted until expiry plus 24 hours;
  - otherwise cache is accepted for 24 hours from `cached_at`.
- Usage is recorded locally by `record_usage()` after access is approved.

Failure behavior:

- Missing license -> `VisionLicenseError::MissingLicense`
- Keygen/network/signature/parse/env failure -> `VisionLicenseError::ValidationFailed(...)`
- Keygen says invalid -> `VisionLicenseError::InvalidLicense`
- Missing `VISION_ANALYSIS` entitlement -> `VisionLicenseError::FeatureNotEnabled`
- Local monthly cap exceeded -> `VisionLicenseError::UsageLimitExceeded`

HTTP mapping in `api.rs::vision`:

- Missing license -> `402 Payment Required`
- Validation failed -> `500 Internal Server Error`
- Invalid license -> `403 Forbidden`
- Feature not enabled -> `403 Forbidden`
- Usage limit exceeded -> `402 Payment Required`
- Body shape is structured JSON:

```json
{
  "error": {
    "code": "MISSING_LICENSE | VALIDATION_ERROR | INVALID_LICENSE | FEATURE_DISABLED | USAGE_LIMIT_EXCEEDED",
    "message": "..."
  }
}
```

Effect on text inference:

- No inspected `/v1/chat/completions` code path calls `VisionLicenseManager`.
- No inspected text inference path reads `SHIMMY_LICENSE_KEY`.
- No inspected text inference path calls Keygen or Stripe directly.
- Therefore license validation affects vision features in inspected files, not OpenAI-compatible text generation.

Cloudflare worker:

- `cloudflare-worker/stripe-keygen-webhook.js` is a separate JavaScript worker.
- It receives Stripe checkout webhooks and creates or looks up Keygen licenses.
- It is not imported by Rust server code in inspected files.
- It is not on the `/v1/chat/completions` path.

## Feature Gating

Cargo features in `Cargo.toml`:

- `default = ["huggingface", "llama"]`
- `llama = ["dep:shimmy-llama-cpp-2"]`
- `huggingface = []`
- `mlx = []`
- `llama-cuda = ["llama", "shimmy-llama-cpp-2/cuda"]`
- `llama-vulkan = ["llama"]`
- `llama-opencl = ["llama"]`
- `fast = ["huggingface"]`
- `full = ["huggingface", "llama", "mlx"]`
- `gpu = ["huggingface", "llama-cuda", "llama-vulkan", "llama-opencl"]`
- `apple = ["huggingface", "mlx"]`
- `coverage = ["huggingface"]`
- `vision = ["dep:image", "dep:base64", "dep:chromiumoxide", "dep:ed25519-dalek", "dep:hex", "dep:sha2"]`

Vision feature boundary:

- `lib.rs` exports `vision` and `vision_license` only with `#[cfg(feature = "vision")]`.
- `server.rs` registers `POST /api/vision` only with `#[cfg(feature = "vision")]`.
- `api.rs::vision` exists only with `#[cfg(feature = "vision")]`.
- `vision.rs` request processing, URL fetching, screenshot capture, MiniCPM download, and license checks exist only with `#[cfg(feature = "vision")]`.

Core inference without license:

- `/v1/chat/completions` can be compiled and executed without the `vision` feature and without a license in inspected files.
- No code evidence shows text inference requiring Keygen, Stripe, or `SHIMMY_LICENSE_KEY`.

Feature-gating risk:

- The default build enables `huggingface` and `llama`, not `vision`.
- `huggingface` is a text backend feature and is enabled by default.
- If a Hugging Face-style model ID is selected, `InferenceEngineAdapter` can route text inference to `HuggingFaceEngine`.
- `HuggingFaceEngine` invokes Python and `transformers.from_pretrained(...)`; external network behavior depends on Python/Transformers cache and environment, not on Rust feature gating alone.

Inference depending on license:

- Text inference license dependency: not verified in inspected files.
- Vision inference license dependency: verified.

## External Network Calls

Rust server outbound HTTP calls found:

| Component | Source | Trigger | Destination | Timeout | Failure handling |
|---|---|---|---|---|---|
| Vision license validation | `vision_license.rs::call_keygen_validate` | `/api/vision` with no valid cache | `https://api.keygen.sh/.../validate-key` | No explicit reqwest timeout found | Error propagates as `VisionLicenseError::ValidationFailed` |
| Vision image URL fetch | `vision.rs::fetch_image_from_url` | `/api/vision` request with `url` and no screenshot path, or screenshot fallback | User-provided HTTP(S) URL after validation | 20 seconds | Error maps through vision error handling; URL size limited |
| Vision screenshot/browser navigation | `vision.rs::capture_screenshot_and_dom` | `/api/vision` with `screenshot=true` or `mode == "web"` | User-provided HTTP(S) URL through headless Chromium | 30-second navigation timeout | Falls back to direct URL image fetch on screenshot failure |
| Vision MiniCPM download | `vision.rs::ensure_download_and_verify` | `/api/vision` built-in `minicpm-v` when files missing and auto-download enabled | Hugging Face model URLs | `SHIMMY_VISION_DOWNLOAD_TIMEOUT_SECS`, default 3600 seconds | SHA256 verified; errors propagate |
| Telemetry | `metrics.rs::TelemetryCollector::send_telemetry` | Only if called and telemetry enabled | `https://metrics.shimmy-ai.dev/v1/usage` | 5 seconds | Silent debug-level failure |

Cloudflare worker outbound HTTP calls:

| Component | Source | Trigger | Destination |
|---|---|---|---|
| License creation | `cloudflare-worker/stripe-keygen-webhook.js::createKeygenLicense` | Stripe checkout webhook | `https://api.keygen.sh/v1/accounts/.../licenses` |
| License lookup | `findLicenseByCheckoutSession`, email lookup path | Success/license/billing flows | `https://api.keygen.sh/v1/accounts/.../licenses...` |
| Stripe line items | `fetchStripeLineItems` | Checkout webhook | `https://api.stripe.com/v1/checkout/sessions/.../line_items` |
| Stripe product | `fetchStripeProduct` | Checkout webhook | `https://api.stripe.com/v1/products/...` |
| Stripe session | `fetchStripeSession` | Success page | `https://api.stripe.com/v1/checkout/sessions/...` |
| Stripe customer | `fetchStripeCustomer`, `createStripeCustomer`, customer lookup | Checkout/customer/billing flows | `https://api.stripe.com/v1/customers...` |
| Stripe checkout | `createStripeCheckoutSession` | Buy endpoint | `https://api.stripe.com/v1/checkout/sessions` |
| Stripe billing portal | billing endpoint | Billing portal flow | `https://api.stripe.com/v1/billing_portal/sessions` |

Text inference route:

- No direct Rust `reqwest`/HTTP call was found in `openai_compat.rs` or the llama/SafeTensors text path inspected in Phase 04.
- `HuggingFaceEngine` can trigger external network indirectly through Python `transformers.from_pretrained(...)` for model/tokenizer load. The actual HTTP implementation is inside Python dependencies, not visible as Rust HTTP code.

Startup:

- No Keygen/Stripe call on text server startup was found in inspected files.
- Telemetry send on startup was not verified in inspected files.
- Vision license cache manager creation may create local directories when `vision` feature is enabled; it does not call Keygen at construction.

Model loading:

- Llama GGUF loading: no outbound HTTP verified in inspected files.
- SafeTensors native loading: no outbound HTTP verified in inspected files.
- HuggingFace loading: Python `from_pretrained(...)` may use network depending on local cache and Transformers settings.
- Vision MiniCPM bootstrap can download model files from Hugging Face during a vision request.

Inference:

- Text llama/SafeTensors generation: no outbound HTTP verified in inspected files.
- Vision URL modes can fetch user-provided URLs during request handling.
- Vision license validation can call Keygen before inference.

Retries:

- No explicit retry policy was found for Keygen validation, vision URL fetch, vision downloads, telemetry, or Cloudflare worker API calls in inspected files.

## Environment Variables Impact

Licensing and paid feature environment variables:

| Env var | Source | Effect | Determinism impact |
|---|---|---|---|
| `SHIMMY_LICENSE_KEY` | `api.rs::vision` | Default license key for `/api/vision` when request license missing | Affects vision access only |
| `KEYGEN_API_KEY` | `vision_license.rs` | Auth token for Keygen validation | Enables remote license validation |
| `KEYGEN_PRODUCT_TOKEN` | `vision_license.rs`, Cloudflare worker | Auth token for Keygen validation/creation | Enables remote Keygen dependency |
| `KEYGEN_ACCOUNT_ID` | Cloudflare worker | Keygen account for worker | Worker only; Rust uses hard-coded account ID |
| `KEYGEN_POLICY_ID` | Cloudflare worker docs/config | License policy setup | Worker only in inspected code |
| `KEYGEN_ADMIN_TOKEN` | Cloudflare worker | Email license lookup endpoint | Worker only |
| `STRIPE_WEBHOOK_SECRET` | Cloudflare worker | Webhook signature verification | Worker only |
| `STRIPE_SECRET_KEY` | Cloudflare worker | Stripe API calls | Worker only |

Vision environment variables:

| Env var | Source | Effect | Determinism impact |
|---|---|---|---|
| `SHIMMY_VISION_MODEL` | `api.rs::vision` | Default vision model | Changes model selection |
| `SHIMMY_VISION_DEV_MODE` | `api.rs::vision` | Exposes server error details in responses | Changes error body detail |
| `SHIMMY_VISION_MAX_LONG_EDGE` | `vision.rs` | Image preprocessing limit | Changes vision input |
| `SHIMMY_VISION_MAX_PIXELS` | `vision.rs` | Image preprocessing limit | Changes vision input |
| `SHIMMY_VISION_TRACE` | `vision.rs` | Enables tracing logs | Observability only |
| `SHIMMY_VISION_AUTO_DOWNLOAD` | `vision.rs` | Enables/disables built-in MiniCPM download | Can trigger external Hugging Face downloads |
| `SHIMMY_VISION_MAX_FETCH_BYTES` | `vision.rs` | Limits remote image fetch size | Changes accepted URL inputs |
| `SHIMMY_VISION_MODEL_DIR` | `vision.rs` | Location for downloaded/built-in vision models | Changes model file source |
| `SHIMMY_VISION_DOWNLOAD_TIMEOUT_SECS` | `vision.rs` | Download timeout for MiniCPM files | Changes external failure timing |

Model discovery and text backend environment variables:

| Env var | Source | Effect | Determinism impact |
|---|---|---|---|
| `SHIMMY_BASE_GGUF` | `main.rs`, `auto_discovery.rs`, `discovery.rs` | Explicit/default model path and discovery parent | Changes available model set |
| `SHIMMY_LORA_GGUF` | `main.rs` | Default LoRA path | Changes loaded model behavior |
| `SHIMMY_MODEL_PATHS` | `main.rs`, `auto_discovery.rs`, `discovery.rs` | Semicolon-separated discovery directories | Changes available model set |
| `OLLAMA_MODELS` | `auto_discovery.rs`, `discovery.rs` | Adds Ollama model directory | Changes available model set |
| `HOME` | `auto_discovery.rs`, `discovery.rs` | Adds user-local model/cache search paths | Changes available model set |
| `USERPROFILE` | `auto_discovery.rs`, `discovery.rs` | Adds Windows user-local model/cache paths | Changes available model set |
| `USERNAME` | `auto_discovery.rs`, `discovery.rs` | Adds Windows drive-based paths | Changes available model set |
| `SHIMMY_BIND_ADDRESS` | `port_manager.rs` | Server bind address override | Affects network exposure/listening address |

Backend selection / hardware environment variables:

| Env var | Source | Effect | Determinism impact |
|---|---|---|---|
| `GGML_CUDA` | `engine/llama.rs` | Set by Shimmy for CUDA backend | Changes llama runtime behavior |
| `GGML_VULKAN` | `engine/llama.rs` | Set by Shimmy for Vulkan backend | Changes llama runtime behavior |
| `VK_ICD_FILENAMES` | `engine/llama.rs` | Existing Vulkan driver override respected | Changes Vulkan backend behavior |
| `GGML_OPENCL` | `engine/llama.rs` | Set by Shimmy for OpenCL backend | Changes llama runtime behavior |
| `GGML_OPENCL_PLATFORM` | `engine/llama.rs` | Defaults to `0` if absent | Changes OpenCL device selection |
| `GGML_OPENCL_DEVICE` | `engine/llama.rs` | Defaults to `0` if absent | Changes OpenCL device selection |

Telemetry and local environment variables:

| Env var | Source | Effect | Determinism impact |
|---|---|---|---|
| `VSCODE_PID` | `metrics.rs` | IDE detection for telemetry payload | Telemetry metadata |
| `TERM_PROGRAM` | `metrics.rs` | IDE detection for telemetry payload | Telemetry metadata |
| `CURSOR_USER_DATA` | `metrics.rs` | IDE detection for telemetry payload | Telemetry metadata |
| `CONTINUE_GLOBAL_DIR` | `metrics.rs` | IDE detection for telemetry payload | Telemetry metadata |
| `NO_COLOR` | `main.rs` | Disables ANSI output | Logging/output only |
| `TERM` | `main.rs` | ANSI output decision | Logging/output only |

Determinism-critical variables for text inference:

- `SHIMMY_BASE_GGUF`
- `SHIMMY_LORA_GGUF`
- `SHIMMY_MODEL_PATHS`
- `OLLAMA_MODELS`
- `HOME`
- `USERPROFILE`
- `USERNAME`
- `SHIMMY_BIND_ADDRESS`
- `GGML_CUDA`
- `GGML_VULKAN`
- `VK_ICD_FILENAMES`
- `GGML_OPENCL`
- `GGML_OPENCL_PLATFORM`
- `GGML_OPENCL_DEVICE`

## External Failure Modes

| Category | Source | Triggering condition | HTTP/status effect | Retry safety |
|---|---|---|---|---|
| `license_validation_failed` | `vision_license.rs::check_vision_access` | Missing license, invalid license, missing entitlement, usage cap exceeded | `/api/vision` returns `402` or `403` structured JSON | No, unless license/config changes |
| `license_validation_failed` | `vision_license.rs::validate_license` | Cache parse/read failure or Keygen response parse/signature/freshness failure | `/api/vision` returns `500` structured JSON with `VALIDATION_ERROR` | Maybe after cache cleanup or clock/network fix |
| `external_service_unavailable` | `vision_license.rs::call_keygen_validate` | Keygen non-2xx or unreachable | `/api/vision` returns `500` validation error | Maybe |
| `network_timeout` | `vision.rs::fetch_image_from_url` | User URL fetch exceeds 20-second timeout | Vision handler maps URL timeout to `504` | Maybe |
| `network_timeout` | `vision.rs::capture_screenshot_and_dom` | Page navigation exceeds 30 seconds | Falls back to image fetch; final status depends on fallback | Maybe |
| `network_timeout` | `vision.rs::ensure_download_and_verify` | MiniCPM Hugging Face download exceeds configured timeout | Vision processing error | Maybe |
| `feature_not_enabled` | `server.rs`, `api.rs`, `vision_license.rs` | `vision` feature not compiled or vision manager missing | `/api/vision` route absent, or manager error if inconsistent state | No without rebuild/config fix |
| `unexpected_external_error` | `metrics.rs::send_telemetry` | Metrics endpoint unavailable or request fails | Silent debug-level failure; no inference impact found | Retry not relevant to inference |
| `unexpected_external_error` | `cloudflare-worker/stripe-keygen-webhook.js` | Stripe/Keygen worker API failure | Worker returns error responses; no Rust text inference impact | Maybe |
| `unexpected_external_error` | `engine/huggingface.rs` | Python `from_pretrained(...)` fails due to cache/network/dependency/model issue | Text load/generation returns error, exposed by OpenAI path as bare `502` per earlier audits | Maybe, but not deterministic |

Timeout gaps:

- Keygen license validation has no explicit reqwest timeout in inspected code.
- Cloudflare worker fetch calls have no explicit timeout in inspected code.
- HuggingFace Python subprocess load/generation has no explicit timeout in inspected code.

## NUCLEO Risk Assessment

Can Shimmy be used fully offline for text inference?

- Yes, only under constrained conditions:
  - use a local backend such as llama GGUF;
  - avoid Hugging Face-style model IDs;
  - do not enable or call vision;
  - do not enable/use telemetry paths;
  - control discovery/model environment variables.

Can licensing logic leak into core text inference paths?

- Not verified in inspected files.
- `VisionLicenseManager` is behind `#[cfg(feature = "vision")]`.
- `/v1/chat/completions` does not call vision/license code in inspected files.
- Shared `AppState` may contain a `vision_license_manager` when compiled with `vision`, but text handlers do not access it.

What must be disabled or ignored:

- Do not call `/api/vision`.
- Do not compile/run with `vision` unless explicitly auditing vision separately.
- Do not use Cloudflare worker surfaces.
- Do not use Stripe/Keygen environment variables in the Shimmy text inference runtime.
- Do not allow Hugging Face-style model IDs if offline determinism is required.
- Do not treat telemetry as part of the inference contract.

Runtime guarantees lost if external services are used:

- Offline operation is lost.
- Request latency becomes dependent on external services.
- Failure modes become non-deterministic.
- Keygen, Stripe, Hugging Face, telemetry, DNS, TLS, and Python package behavior can affect outcomes.
- Error bodies at the OpenAI text boundary remain too coarse to distinguish many external backend failures.

Risk classification:

CRITICAL:

- HuggingFace is enabled by default and can be selected by model ID shape.
- HuggingFace backend can invoke Python model loading that may use external network/cache behavior.
- Vision feature can call Keygen and Hugging Face during request handling.
- Keygen validation has no explicit timeout in inspected code.
- Text OpenAI path maps backend failures to bare `502`, so external HuggingFace failures are not distinguishable at HTTP level.

INFORMATIVE:

- Keygen/Stripe licensing is not directly on the inspected `/v1/chat/completions` path.
- Vision route registration is compile-time gated by `vision`.
- Cloudflare worker is separate from Rust server runtime in inspected files.
- Telemetry sender exists and uses a 5-second timeout, but no production invocation was found in inspected server/main files.
- Vision URL fetching includes SSRF-style checks against localhost/private IPs.

PREMATURE:

- Treating vision licensing as a blocker for text-only local GGUF inference.
- Depending on Shimmy vision behavior in NUCLEO hardening.
- Assuming HuggingFace backend is offline-safe without controlling Python/Transformers environment.
- Using Cloudflare worker behavior as part of Shimmy inference availability.

## Required Adapter Constraints

Feature constraints:

- Use text-only Shimmy runtime for NUCLEO evaluation.
- Do not call `/api/vision`.
- Do not call Cloudflare worker endpoints.
- Do not use `/api/tools`, `/api/workflows/execute`, or non-OpenAI inference surfaces, as established in earlier phases.
- Treat `vision` as forbidden for HARDENING unless separately audited and isolated.

Model/backend constraints:

- Use an explicit NUCLEO-owned model allowlist.
- Prefer local GGUF model IDs that route to llama backend.
- Reject Hugging Face-style model IDs if offline operation is required.
- Reject `.safetensors` as production text inference unless its placeholder behavior is explicitly accepted, per Phase 04.
- Treat every unknown backend selection as unsafe.

Environment constraints:

- Pin or clear model discovery variables:
  - `SHIMMY_BASE_GGUF`
  - `SHIMMY_LORA_GGUF`
  - `SHIMMY_MODEL_PATHS`
  - `OLLAMA_MODELS`
  - `HOME`
  - `USERPROFILE`
  - `USERNAME`
- Pin bind address through controlled config, not ambient environment drift.
- Pin hardware variables if GPU is allowed:
  - `GGML_CUDA`
  - `GGML_VULKAN`
  - `VK_ICD_FILENAMES`
  - `GGML_OPENCL`
  - `GGML_OPENCL_PLATFORM`
  - `GGML_OPENCL_DEVICE`
- Do not set vision/license variables in the text inference runtime:
  - `SHIMMY_LICENSE_KEY`
  - `KEYGEN_API_KEY`
  - `KEYGEN_PRODUCT_TOKEN`
  - `SHIMMY_VISION_*`

External call constraints:

- Block outbound network from the Shimmy process when evaluating offline text inference.
- If network cannot be blocked, log and monitor outbound attempts at the process/container boundary.
- Do not rely on Shimmy to prevent Python/Transformers network calls when HuggingFace backend is available.
- Do not rely on Rust code inspection alone to prove HuggingFace offline behavior.

Error normalization constraints:

- Map license errors only if a forbidden vision route is accidentally called.
- Map unexpected Keygen/Stripe/worker contact as `unexpected_external_error` for this audit taxonomy.
- Map HuggingFace Python/network/cache failures surfaced through `/v1/chat/completions` as `unknown_backend_error` or backend-specific load/generation failure only if phase instrumentation can distinguish them.
- Preserve earlier Phase 02/03/04 constraints:
  - `stream:false`
  - strict request validation
  - response schema validation
  - adapter-side timeouts
  - one in-flight request per Shimmy instance unless concurrency is separately proven.

Observability requirements:

- Log whether `vision` feature is enabled in the Shimmy binary if discoverable.
- Log selected model ID and whether it is local allowlisted.
- Log whether model ID shape would route to HuggingFace.
- Log backend base URL/process identity.
- Log outbound-network policy status for the Shimmy process.
- Log environment fingerprint for model/hardware variables, without logging license keys or secrets.

## Final Classification (safe / risky / requires isolation)

Classification: **risky / requires isolation**

CRITICAL:

- Text inference is license-isolated in inspected Rust code, but not fully external-dependency-isolated unless backend/model/environment are constrained.
- Default `huggingface` feature creates an external dependency risk for text inference through Python `from_pretrained(...)`.
- Vision feature introduces Keygen validation, user URL fetches, browser navigation, and Hugging Face downloads.
- Keygen validation has no explicit timeout in inspected code.
- External backend failures still collapse into coarse OpenAI route errors.

INFORMATIVE:

- Keygen and Stripe are not on the inspected `/v1/chat/completions` text path.
- Stripe/Keygen worker is a separate Cloudflare Worker artifact.
- Vision route is compile-time gated.
- Text inference can be offline with local GGUF and constrained environment.

PREMATURE:

- Auditing or hardening Shimmy vision for NUCLEO text backend use.
- Allowing HuggingFace model IDs before proving offline/cache behavior.
- Depending on Shimmy telemetry, worker, or license system for inference readiness.
