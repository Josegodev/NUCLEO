# Shimmy Phase 03 Model Runtime and Resource Audit

## Summary

Scope inspected:

- `runtime_lab/audit/shimmy_phase_01_entrypoints.md`
- `runtime_lab/audit/shimmy_phase_02_api_error_mapping.md`
- `external/shimmy/src/model_manager.rs`
- `external/shimmy/src/model_registry.rs`
- `external/shimmy/src/auto_discovery.rs`
- `external/shimmy/src/discovery.rs`
- `external/shimmy/src/preloading.rs`
- `external/shimmy/src/safetensors_adapter.rs`
- `external/shimmy/src/server.rs`
- `external/shimmy/src/openai_compat.rs`
- `external/shimmy/src/api.rs`, secondary scope, for native route comparison and load/unload placeholders.
- `external/shimmy/src/error.rs`, secondary scope, for typed error inventory.
- `external/shimmy/src/metrics.rs`, secondary scope, for resource and shell-out behavior.

No source code was modified.

Phase 03 conclusion:

Shimmy model discovery is environment-dependent and can mix local folders, Hugging Face cache paths, LM Studio folders, Shimmy folders, and Ollama models. Discovery is not stable enough to be the sole authority for NUCLEO model availability. NUCLEO should require its own model allowlist if Shimmy is ever wrapped behind an adapter.

For the OpenAI-compatible route, model loading is lazy at request time. `POST /v1/chat/completions` calls `state.engine.load(&spec).await` for each request path before generation. In inspected files, this route does not use `ModelManager` or `SmartPreloader` caches. Whether the concrete engine internally caches loaded models is not verified in inspected files.

Load failure and non-stream generation failure are distinguishable by source line in `openai_compat.rs`, but both return bare `502 Bad Gateway` to the HTTP client. A NUCLEO adapter cannot distinguish them from HTTP shape alone unless it controls call phase internally or Shimmy changes the error envelope.

## Model Discovery

Primary discovery path used by the registry:

- `model_registry.rs::Registry::with_discovery()`
- `model_registry.rs::Registry::refresh_discovered_models()`
- `auto_discovery.rs::ModelAutoDiscovery::new()`
- `auto_discovery.rs::ModelAutoDiscovery::discover_models()`

Search paths in `ModelAutoDiscovery::new()`:

- `./models`
- Parent directory of `SHIMMY_BASE_GGUF`, if set.
- Semicolon-separated directories from `SHIMMY_MODEL_PATHS`, if set.
- `OLLAMA_MODELS`, if set.
- From `HOME`:
  - `~/.cache/huggingface/hub`
  - `~/.ollama/models`
  - `~/.lmstudio/models`
  - `~/models`
  - `~/.local/share/shimmy/models`
- From `USERPROFILE`:
  - `.cache\huggingface\hub`
  - `.ollama\models`
  - `.lmstudio\models`
  - `models`
  - `AppData\Local\shimmy\models`
  - `Downloads`
- On Windows, additional drive-based paths:
  - `C:\Users\<USERNAME>\AppData\Local\Ollama\models`
  - `D:\Users\<USERNAME>\AppData\Local\Ollama\models`
  - `E:\Users\<USERNAME>\AppData\Local\Ollama\models`
  - `F:\Users\<USERNAME>\AppData\Local\Ollama\models`
  - `C:\Ollama\models`, `D:\Ollama\models`, `E:\Ollama\models`, `F:\Ollama\models`
  - `C:\models`, `D:\models`, `E:\models`, `F:\models`

Discovery behavior:

- `discover_models()` scans existing directories only.
- Directory scan failures are logged to stderr and skipped.
- Ollama discovery failures are logged to stderr and skipped.
- Recursive local scanning is depth-limited to 4.
- Ollama direct recursive scanning is depth-limited to 5.
- Hidden/system/build/cache-like directories are skipped by name.
- GGUF files are accepted.
- SafeTensors files are accepted unless the path contains `tokenizer` or `config`.
- `.bin` files are accepted only when their path looks model-like and not build/cache/tokenizer/config-like.
- Sharded model files matching `model-00001-of-00004.ext` are grouped.
- LoRA files may be paired by same-directory filename heuristics.
- Duplicates are removed by path equality after sorting by path.

Determinism assessment:

- Discovery order is partially normalized by sorting/deduping discovered models by path.
- Registry storage uses `HashMap`, so insertion collision behavior is deterministic by key overwrite semantics but not by stable source priority when duplicate names are inserted from differently ordered discovery results.
- Filesystem contents, env vars, user home, external caches, and Ollama manifests can change without code changes.
- Therefore discovery can change between runs without code/config changes.

Can Ollama, Hugging Face, and local folders be mixed?

- Yes. The same discovery pass includes local paths, Hugging Face cache paths, LM Studio paths, Shimmy paths, and Ollama-specific manifest/direct discovery.

What happens if no models are found?

- In `model_registry.rs`, `list_all_available()` returns an empty list if both manual and discovered maps are empty.
- In `openai_compat.rs::models`, `/v1/models` would return `"data":[]`.
- In `openai_compat.rs::chat_completions`, an unknown model maps to `404` structured model-not-found JSON.
- Startup process behavior when no models are found was documented in Phase 01 from `main.rs`, but `main.rs` is not in Phase 03 scope; further startup behavior is not verified in inspected files.

`discovery.rs` note:

- `discovery.rs::ModelDiscovery` is a separate discovery implementation using `SHIMMY_BASE_GGUF`, `SHIMMY_MODEL_PATHS`, `OLLAMA_MODELS`, `HOME`, and `USERPROFILE`.
- It prints debug messages during discovery.
- It is not the discovery implementation directly imported by `model_registry.rs` in inspected files. The OpenAI-compatible route reaches `auto_discovery.rs` through `model_registry.rs`, not `discovery.rs`.

## Model Registry and Model IDs

Registry structure:

- Manual models are stored in `Registry.inner: HashMap<String, ModelEntry>`.
- Discovered models are stored in `Registry.discovered_models: HashMap<String, DiscoveredModel>`.

Model ID creation:

- Manual models use `ModelEntry.name`.
- Non-sharded discovered model names are generated from filename:
  - file extension removed;
  - underscores and spaces replaced with dashes;
  - lowercased.
- Sharded discovered model names use the directory name, falling back to grouped filename key.
- Ollama manifest model names are built from manifest path components.
- Ollama direct model names may be prefixed with `ollama:`.

Duplicate/collision behavior:

- `Registry::register()` inserts by `ModelEntry.name`; same key overwrites previous manual entry.
- `refresh_discovered_models()` inserts discovered models by `model.name`; same discovered name overwrites previous discovered entry.
- `auto_register_discovered()` inserts discovered models into manual registry only if the manual registry does not already contain that name.
- `list_all_available()` combines manual keys and discovered keys, sorts, and deduplicates names.
- `to_spec()` checks manual entries first, then discovered entries.

Implication:

- Manual model entries take precedence for `to_spec()`.
- `/v1/models` hides manual/discovered source conflicts because it returns a deduplicated list of names.
- Duplicate discovered names can collide silently in the discovered `HashMap`.

Is `/v1/models` stable enough for NUCLEO model listing?

- Stable enough only as a discovery hint.
- Not stable enough as an authorization source or deterministic model policy source.

Should NUCLEO trust Shimmy model IDs?

- No. NUCLEO should require its own allowlist.
- Reason: Shimmy model IDs can be created from filesystem names, Ollama manifests, local user folders, and environment-dependent discovery paths.

## Model Loading Behavior

OpenAI-compatible request path:

- `openai_compat.rs::chat_completions` calls `state.registry.to_spec(&req.model)`.
- If a spec is found, it calls `state.engine.load(&spec).await`.
- If loading succeeds, it calls `loaded.generate(...)`.

Loading mode:

- Lazy at request time for `/v1/chat/completions`.
- No eager loading is visible in this handler.
- No use of `ModelManager` or `SmartPreloader` is visible in this handler.

Function that loads the model:

- At the audited HTTP boundary: `state.engine.load(&spec).await`.
- The concrete engine implementation is not in the requested Phase 03 scope; actual backend load internals are not verified in inspected files.

Can load failure be distinguished from generation failure?

- Inside `openai_compat.rs`, yes:
  - load failure occurs at `engine.load(&spec).await`;
  - generation failure occurs at `loaded.generate(&prompt, opts, None).await`.
- At HTTP response level, no:
  - both return bare `502 Bad Gateway` for non-streaming requests.

Are loaded models cached?

- In `openai_compat.rs`, no cache is used explicitly.
- `ModelManager` has metadata tracking but does not store actual `LoadedModel` instances.
- `SmartPreloader` stores `Arc<dyn LoadedModel>` in `loaded_models`.
- No inspected route wires `SmartPreloader` into `/v1/chat/completions`.
- Whether `state.engine.load()` internally caches is not verified in inspected files.

Can models be unloaded?

- `api.rs::unload_model` is a placeholder route returning `"status":"pending"`.
- `ModelManager::unload_model()` removes metadata from its internal map.
- `SmartPreloader::clear()` clears loaded models and stats.
- No verified unload behavior exists for the `/v1/chat/completions` loaded model path in inspected files.

Shared mutable state:

- `AppState` contains `engine`, `registry`, observability, and response cache according to earlier audited files, but detailed engine internals are not in this scope.
- `Registry` is shared behind `Arc<AppState>` but is not mutated by `/v1/chat/completions`.
- `ModelManager` uses `Arc<RwLock<HashMap<...>>>`.
- `SmartPreloader` uses `Arc<RwLock<HashMap<...>>>` and `Arc<Mutex<VecDeque<...>>>`.
- The OpenAI-compatible route itself does not use those manager/preloader locks in inspected files.

Concurrency implications:

- Concurrent `/v1/chat/completions` requests can concurrently call `state.engine.load(&spec).await`.
- Whether the concrete engine serializes, caches, duplicates, or races model loads is not verified in inspected files.
- If `engine.load()` is expensive and uncached, concurrent requests to the same model may duplicate loading work. This is not verified in inspected files.

## Inference Execution

Function that generates text:

- Non-streaming OpenAI-compatible route calls `loaded.generate(&prompt, opts, None).await`.
- Streaming OpenAI-compatible route calls `loaded.generate(&prompt_clone, opts_clone, Some(callback)).await` inside `tokio::spawn`.
- Concrete generation internals are not verified in inspected files.

Parameters affecting generation:

- `temperature`
- `top_p`
- `max_tokens`
- `stream`
- `stop_tokens`

Application of parameters:

- `temperature`, if present, directly assigns `opts.temperature`.
- `top_p`, if present, directly assigns `opts.top_p`.
- `max_tokens`, if present, directly assigns `opts.max_tokens`.
- `stream`, if present, directly assigns `opts.stream`.
- Stop tokens start from template family defaults and then append user-provided `stop`.

Range validation:

- No range validation for `temperature`, `top_p`, or `max_tokens` is present in `openai_compat.rs`.
- Serde type parsing rejects structurally invalid types before the handler body, but exact HTTP rejection body is not verified in inspected files.

Empty prompt/messages/invalid options:

- `messages` is required by struct type.
- Empty `messages: []` is not rejected in `openai_compat.rs`.
- Invalid roles are not rejected.
- Empty content strings are not rejected.
- If there is no user message, fallback prompt rendering uses all pairs as history.
- Numeric option ranges are not checked in inspected handler.

Generation error typing:

- `loaded.generate(...)` errors are collapsed to bare `502` in non-streaming mode.
- Streaming generation errors are ignored because the result is assigned to `_`, then a final chunk and `[DONE]` are sent.
- `error.rs` defines typed errors including `GenerationError`, `ModelLoadError`, `BackendNotAvailable`, `ConfigError`, and others, but `openai_compat.rs` does not expose those as structured HTTP responses.

## Resource Controls

Verified controls in inspected files:

- `ModelEntry.ctx_len: Option<usize>`.
- `ModelEntry.n_threads: Option<i32>`.
- Discovered models converted to specs default to `ctx_len: 8192` and `n_threads: None`.
- Manual entries preserve configured `ctx_len` and `n_threads`, with `ctx_len` falling back to `8192`.
- `PreloadConfig` in `model_manager.rs` includes:
  - `enabled`
  - `max_preloaded_models`
  - `max_memory_mb`
  - `preload_threshold_score`
  - `min_usage_for_preload`
  - `cleanup_interval`
- `PreloadingConfig` in `preloading.rs` includes:
  - `max_loaded_models`
  - `min_usage_threshold`
  - `model_ttl`
  - `enable_warmup`
  - `warmup_prompt`
  - `warmup_max_tokens`

Important limitation:

- `ModelManager::load_model()` stores `ModelLoadInfo`, not an actual loaded model object.
- `PreloadConfig.max_memory_mb` is reported in stats but no actual memory measurement enforcement is visible in `model_manager.rs`.
- `SmartPreloader` enforces only loaded model count in inspected code, not measured memory.
- No inspected `/v1/chat/completions` path uses these preloading controls.

CPU/GPU controls:

- In inspected Phase 03 files, CPU/GPU backend selection for inference is not verified.
- Prior audits observed CLI/backend selection outside this Phase 03 primary scope, but concrete engine resource behavior is not verified in inspected files.
- `server.rs::metrics_endpoint` detects GPU by shelling out, but that is metrics behavior, not an inference control.

Offloading controls:

- Not verified in inspected files for the OpenAI-compatible route.

Context size, batch size, memory limits, threading:

- Context size and thread count exist in `ModelSpec` construction via registry.
- Batch size controls are not verified in inspected files.
- Hard memory limits for actual inference are not verified in inspected files.
- Threading behavior in the concrete engine is not verified in inspected files.

Global, per-model, or per-request:

- `ctx_len` and `n_threads` are per model spec.
- `temperature`, `top_p`, `max_tokens`, `stream`, and `stop` are per request.
- Discovery paths are process/environment-level.
- Preloading configs are manager/preloader-level, but not verified as active for `/v1/chat/completions`.

Environment-dependent behavior:

- Discovery depends on `SHIMMY_BASE_GGUF`, `SHIMMY_MODEL_PATHS`, `OLLAMA_MODELS`, `HOME`, `USERPROFILE`, and Windows `USERNAME`.
- Metrics/telemetry code checks editor/environment variables such as `VSCODE_PID`, `TERM_PROGRAM`, `CURSOR_USER_DATA`, and `CONTINUE_GLOBAL_DIR`.
- GPU detection depends on installed system commands and platform.

Shell-outs outside metrics:

- `server.rs` metrics helper shells out to `nvidia-smi`, `rocm-smi`, and `wmic`.
- `metrics.rs` shells out to GPU/system commands including `nvidia-smi`, `rocm-smi`, `rocminfo`, `wmic`, and `lspci`.
- `safetensors_adapter.rs` shells out to `which` and `python` when attempting SafeTensors-to-GGUF conversion.

## Runtime Reliability

Possible startup failure modes:

- `server.rs::run` can fail to bind the TCP listener.
- Startup behavior for invalid CLI flags, invalid model paths, no models, or engine initialization is not verified in Phase 03 inspected files.
- Phase 01 documented no-model startup exit from `main.rs`; `main.rs` was not in Phase 03 scope.

Possible request-time failure modes:

- Invalid JSON or wrong schema rejected by Axum extractor; exact body not verified in inspected files.
- Requested model not found in registry: structured `404`.
- `engine.load(&spec).await` fails: bare `502`.
- `loaded.generate(...).await` fails in non-streaming mode: bare `502`.
- Streaming generation failure: swallowed and converted into normal-looking stream termination.
- Stream chunk serialization failure: event data becomes `{}`.
- Prompt formatting may behave unexpectedly if the last user message is not the final message.
- Discovery can silently skip unreadable directories or failed Ollama discovery.
- SafeTensors conversion may execute external scripts if called; whether this occurs on `/v1/chat/completions` is not verified in inspected files.

Hidden state or implicit behavior:

- Model discovery includes broad user-local folders and caches.
- Registry silently overwrites duplicate discovered names.
- `/v1/models` hides manual/discovered source conflicts through deduplication.
- Template family may be inferred from model name when spec template is absent or unknown.
- Stop tokens are auto-added from template family before appending user-provided stop tokens.
- `created` timestamps in `/v1/models` and completions are current wall-clock values, not stable model metadata.

Timeout/cancellation behavior:

- No request timeout is implemented in `openai_compat.rs`.
- No generation cancellation handling is visible in `openai_compat.rs`.
- `metrics.rs` telemetry send uses a 5-second timeout, but that is telemetry, not inference.
- NUCLEO-side timeout behavior is required.

Concurrent requests to same model:

- Safety is unclear.
- `openai_compat.rs` allows concurrent calls into shared `state.engine`.
- Engine trait implementation and internal synchronization are not verified in inspected files.
- No per-model request lock is visible at the HTTP handler level.

## Concurrency Assessment

Verified:

- Axum handler receives shared `Arc<AppState>`.
- Registry is read-only in `/v1/chat/completions`.
- Each request calls `engine.load(&spec).await` before generation.
- Streaming spawns a background task.
- ModelManager and SmartPreloader use async locks internally.

Not verified in inspected files:

- Whether `InferenceEngine` is safe for concurrent load calls.
- Whether `LoadedModel` is safe for concurrent generation.
- Whether model memory is shared, duplicated, or cached.
- Whether simultaneous same-model requests are serialized.
- Whether cancellation drops an in-progress backend generation.

Concurrency risk:

- Without verified engine-level serialization/caching, a NUCLEO adapter should assume concurrent same-model requests may contend for CPU/GPU/RAM and may duplicate load work.

## NUCLEO Adapter Requirements

Required validations before request:

- Require a NUCLEO-owned model allowlist.
- Reject any model ID not present in that allowlist before calling Shimmy.
- Require `stream: false`.
- Require non-empty `messages`.
- Validate supported roles.
- Validate non-null string content.
- Validate `temperature`, `top_p`, and `max_tokens` ranges according to NUCLEO policy.
- Reject unsupported OpenAI fields at the adapter boundary.
- Do not rely on Shimmy `usage` values.

Required timeout policies:

- Health timeout.
- Model listing timeout.
- Model load/generation timeout for `/v1/chat/completions`.
- Separate connection timeout and full-response timeout.
- Treat NUCLEO-side timeout as `timeout`, not as Shimmy structured failure.

Required model allowlist policy:

- Do not trust `/v1/models` as authorization.
- Treat `/v1/models` as discovery only.
- Resolve model IDs through NUCLEO config.
- Optionally compare Shimmy-listed IDs against NUCLEO allowlist for observability.

Required error mappings:

- Unknown model before request: adapter-side `model_not_found` or `unsupported_feature`, depending on NUCLEO policy.
- Shimmy `404` model error: `model_not_found`.
- Shimmy `502` immediately after generation request: map by adapter call phase if possible:
  - load phase known: `model_load_failed`;
  - generate phase known: `generation_failed`;
  - otherwise `unknown_backend_error`.
- Connection refused/process unavailable: `backend_unavailable`.
- Timeout: `timeout`.
- HTTP `200` with invalid schema: `malformed_response`.
- Streaming response when non-streaming requested: `malformed_response`.

Forbidden Shimmy behaviors:

- Do not call native `/api/generate`.
- Do not call `/ws/generate`.
- Do not call Shimmy tool or workflow routes.
- Do not call placeholder load/unload/status routes as authoritative lifecycle controls.
- Do not allow Shimmy discovery to expand NUCLEO model policy automatically.
- Do not allow `stream:true` in HARDENING.

Observability fields NUCLEO should log:

- Shimmy base URL or backend instance ID.
- Requested model ID.
- Whether requested model ID was allowlisted.
- Route used.
- Request timeout budget.
- HTTP status.
- Error mapping result.
- Whether response passed schema validation.
- Response latency.
- Whether model list contained requested model.
- Shimmy `id` from completion response, if present.
- Assistant content length, not raw prompt or raw response unless explicitly allowed by NUCLEO privacy policy.

## Risks Classified

CRITICAL:

- Discovery is environment-dependent and can change between runs without code changes.
- Model IDs can collide silently across manual and discovered sources.
- `/v1/models` is not sufficient as an authorization or deterministic model policy source.
- `/v1/chat/completions` returns bare `502` for both load and generation failures.
- `stream:true` swallows generation failures and can appear successful.
- Concurrent same-model request safety is not verified in inspected files.

INFORMATIVE:

- `/v1/chat/completions` uses lazy request-time loading at the HTTP handler boundary.
- Usage token counts are placeholder zeros.
- Template and stop-token behavior is inferred from model spec/name.
- `ModelManager` and `SmartPreloader` exist, but they are not wired into the inspected OpenAI-compatible route.
- Metrics and SafeTensors conversion code can shell out to system commands.
- `discovery.rs` appears separate from the registry path used by `/v1/models`.

PREMATURE:

- Changing Shimmy discovery or registry behavior.
- Depending on Shimmy preloading before verifying whether production routes use it.
- Using Shimmy load/unload/status routes as lifecycle control.
- Supporting streaming in a NUCLEO adapter.
- Trusting concrete engine caching behavior before inspecting engine implementation.

## Open Questions for Phase 04

- What concrete type implements `InferenceEngine` in the server path?
- Does `engine.load(&spec)` cache loaded models internally?
- Is `LoadedModel::generate` safe for concurrent calls?
- Does the concrete engine serialize access to llama.cpp or other backends?
- Are `ctx_len` and `n_threads` actually honored by the backend implementation?
- Are GPU backend and MoE/offload options global, per engine, or per request?
- Can load errors be made distinguishable at the adapter boundary without changing Shimmy?
- Does SafeTensors conversion run in normal model load paths or only in explicit adapter functions?
- What is the maximum safe request concurrency per Shimmy instance?
- What exact timeout values should NUCLEO enforce for health, model listing, load, and generation?
