# Shimmy Phase 04 Engine, Concurrency, and Memory Audit

## Summary

Scope inspected:

- `runtime_lab/audit/shimmy_phase_01_entrypoints.md`
- `runtime_lab/audit/shimmy_phase_02_api_error_mapping.md`
- `runtime_lab/audit/shimmy_phase_03_model_runtime_resources.md`
- `external/shimmy/src/lib.rs`
- `external/shimmy/src/main.rs`
- `external/shimmy/src/server.rs`
- `external/shimmy/src/model_manager.rs`
- `external/shimmy/src/preloading.rs`
- `external/shimmy/src/safetensors_adapter.rs`
- `external/shimmy/src/engine/mod.rs`
- `external/shimmy/src/engine/adapter.rs`
- `external/shimmy/src/engine/llama.rs`
- `external/shimmy/src/engine/safetensors_native.rs`
- `external/shimmy/src/engine/huggingface.rs`
- `external/shimmy/src/engine/mlx.rs`
- `external/shimmy/src/engine/universal.rs`
- `external/shimmy/Cargo.toml`

No source code was modified.

Core finding:

The concrete engine behind `state.engine.load(&spec).await` is `InferenceEngineAdapter`. It is instantiated once into `AppState` for the server path, but it does not cache loaded models. `InferenceEngineAdapter::load()` selects a backend and loads directly on each call.

For the default feature set, `Cargo.toml` enables `huggingface` and `llama`. Local `.gguf` paths route to `LlamaEngine`; `.safetensors` paths route to `SafeTensorsEngine`; Hugging Face-style IDs can route to `HuggingFaceEngine`.

The high-risk backend for real local inference is `LlamaEngine`. Each `load()` creates a new `LlamaModel` and `LlamaContext`, then returns a new `LlamaLoaded`. `LlamaLoaded` protects its own llama context with a `Mutex`, but because the OpenAI path reloads per request, that mutex does not serialize concurrent loads of the same model across requests.

Final classification: **risky / requires isolation**.

## Engine Implementation

Trait definitions:

- `engine/mod.rs::InferenceEngine`
- `engine/mod.rs::LoadedModel`

Concrete engine used by server:

- `engine/adapter.rs::InferenceEngineAdapter`

Where it is instantiated:

- `main.rs` constructs `Box<dyn engine::InferenceEngine>` using `InferenceEngineAdapter::new_with_backend(cli.gpu_backend.as_deref())`.
- If MoE flags are supplied and `llama` is compiled, `with_moe_config()` is applied.
- During serve startup, `main.rs` may construct a second enhanced adapter when auto-registering discovered models. That enhanced state is the one passed to `server::run`.

Global or multiple:

- One adapter instance is stored in the active `AppState` for the running server.
- The llama.cpp backend object itself is global through `LLAMA_BACKEND: OnceLock`.
- Loaded model instances are not global in the inspected OpenAI path.

Shared across requests:

- `AppState` is shared through `Arc<AppState>`.
- `state.engine` is shared across requests.
- Loaded models returned by `engine.load()` are per call in the inspected OpenAI path.

## Model Loading Internals

`InferenceEngineAdapter::load()` behavior:

- Calls `select_backend(spec)`.
- Routes:
  - `.safetensors` -> `SafeTensorsEngine`
  - `.gguf` -> `LlamaEngine` when `llama` feature is enabled
  - `.npz` or `.mlx` -> `MLXEngine` when `mlx` feature is enabled
  - Hugging Face-style model IDs -> `HuggingFaceEngine`
  - Ollama blobs -> `LlamaEngine` when `llama` feature is enabled
  - model names containing `llama`, `phi`, `qwen`, `gemma`, or `mistral` -> `LlamaEngine` when available

Important code evidence:

- `InferenceEngineAdapter` has a comment: `loaded_models removed as caching is not currently implemented`.
- `InferenceEngineAdapter::load()` has a comment: `load model directly (no caching for now to avoid complexity)`.

Does it cache models?

- Adapter-level caching: no.
- Llama backend caching of loaded models: no cache found in inspected `LlamaEngine`.
- SafeTensors cache: commented out / disabled.
- HuggingFace cache: no Rust-side loaded-model cache; each generation spawns Python and loads model inside the Python script.
- MLX cache: no cache found; implementation is placeholder.

Where are loaded models stored?

- For `LlamaEngine`, each `load()` returns a new `LlamaLoaded` containing:
  - `LlamaModel`
  - `LlamaContext`
  - optional native chat template
- For `SafeTensorsEngine`, each `load()` returns a new `SafeTensorsModel` containing:
  - in-memory or memory-mapped model data
  - config
  - tokenizer
- For `HuggingFaceEngine`, `load()` returns a `HuggingFaceModel` containing identifiers and Python path, not a persistent loaded Python model in Rust.
- For `MLXEngine`, `load()` returns an `MLXModel` placeholder with name/path/context length.

Map keyed by model name/path:

- No active map in `InferenceEngineAdapter`.
- `ModelManager` and `SmartPreloader` contain maps, but they are not wired into the OpenAI path in inspected files.

Concurrent same-model load:

- There is no per-model load lock in `InferenceEngineAdapter`.
- There is no global load serialization in `LlamaEngine` beyond one-time backend initialization.
- Two concurrent requests can call `LlamaModel::load_from_file(...)` for the same path at the same time.
- Actual llama.cpp behavior under concurrent same-model loads is not verified in inspected files.

## LoadedModel Lifecycle

`LoadedModel`:

- Trait with async `generate(...)`.
- Optional default `generate_vision(...)`.
- Optional `format_prompt(...)`.

Llama lifecycle:

- `LlamaEngine::load()` calls global `get_or_init_backend()`.
- It loads the model using `LlamaModel::load_from_file(...)`.
- It creates a new context using `model.new_context(...)`.
- It attaches LoRA if provided and not SafeTensors.
- It transmutes context lifetime to `'static`.
- It returns `Box<dyn LoadedModel>` containing `LlamaLoaded`.

Memory ownership:

- `LlamaLoaded` owns `LlamaModel` and `LlamaContext`.
- It is boxed and returned to the request handler.
- In non-streaming OpenAI path, the loaded object is dropped when request handling completes.
- In streaming OpenAI path, the loaded object is moved into a spawned task and dropped when that task completes.

Reference counted or copied:

- `LlamaLoaded` is returned as `Box<dyn LoadedModel>`, not `Arc`.
- No sharing of a loaded llama model between requests is visible in inspected OpenAI path.

Explicit unload/drop:

- No explicit unload call for `LlamaLoaded`.
- Memory release depends on Rust drop of `LlamaLoaded` and underlying llama binding destructors.
- Deterministic Rust drop at end of owner lifetime exists, but actual native memory release behavior is delegated to `shimmy-llama-cpp-2` and not verified in inspected files.

Thread safety:

- `LlamaLoaded` wraps context in `std::sync::Mutex`.
- It uses `unsafe impl Send` and `unsafe impl Sync`.
- Comment states llama.cpp model/context use raw pointers and are `!Send` by default, and that FFI calls are made while holding the mutex.
- This serializes access inside one `LlamaLoaded` instance only.

## Caching Behavior

Active adapter cache:

- None.

LRU or similar cache:

- `preloading.rs::SmartPreloader` implements a loaded model map and LRU-like state.
- `model_manager.rs::ModelManager` implements metadata maps and a preload queue.
- Neither is used by `openai_compat.rs` or `InferenceEngineAdapter` in inspected files.

Cache size bounded:

- `SmartPreloader` has `max_loaded_models`.
- `ModelManager` has `max_preloaded_models`.
- These bounds do not apply to the OpenAI-compatible request path unless wired elsewhere; not verified in inspected files.

Eviction implemented:

- `SmartPreloader::enforce_memory_limits()` evicts by count, not measured memory.
- `ModelManager::cleanup_old_models()` removes metadata by age/access count.
- Not active in OpenAI path in inspected files.

Can caching be trusted?

- No. Caching must be ignored for `/v1/chat/completions` based on inspected code.

## Concurrency Model

Engine thread safety:

- `InferenceEngine` requires `Send + Sync`.
- `LoadedModel` requires `Send + Sync`.
- `InferenceEngineAdapter` contains backend engines and no active cache/mutex.
- `LlamaLoaded` uses a mutex around its context.

Parallel generation on same model:

- If the same `LlamaLoaded` instance were shared, generation would serialize on its context mutex.
- In the inspected OpenAI path, loaded models are not shared; each request loads its own `LlamaLoaded`.
- Therefore concurrent requests to the same model are not serialized by `LlamaLoaded`'s mutex.

Internal queueing:

- No queueing in `InferenceEngineAdapter`.
- No per-model lock in `openai_compat.rs`.
- No global generation semaphore found in inspected files.

Under concurrent load:

- Multiple requests can trigger simultaneous model loads.
- Multiple loaded model instances can exist for the same model path.
- This can duplicate RAM/VRAM pressure.
- Exact native backend behavior under this pressure is not verified in inspected files.

Safe concurrency level:

- For hardening, treat safe concurrency as **1 request per Shimmy instance or 1 request per model enforced externally**.
- Higher concurrency is not proven safe in inspected files.

## GPU/CPU Execution Model

Backend selection:

- Default features: `huggingface`, `llama`.
- `.gguf` local files use llama backend when compiled.
- `.safetensors` files use native SafeTensors engine.
- Hugging Face IDs can use Python-based HuggingFace engine.
- MLX requires `mlx` feature and Apple Silicon/macOS checks.

Llama CPU/GPU behavior:

- `LlamaEngine` stores `GpuBackend`.
- CLI backend string flows into `InferenceEngineAdapter::new_with_backend(...)`, then `LlamaEngine::new_with_backend(...)`.
- Supported configured strings:
  - `auto`
  - `cpu`
  - `cuda`, if compiled with `llama-cuda`
  - `vulkan`, if compiled with `llama-vulkan`
  - `opencl`, if compiled with `llama-opencl`
- If GPU feature is not compiled, requesting that backend logs a warning and falls back to auto-detect.

GPU detection:

- CUDA detection shells out to `nvidia-smi`.
- Vulkan detection shells out to `vulkaninfo --summary`, otherwise assumes available if feature is enabled.
- OpenCL detection shells out to `clinfo`; on Windows checks `where OpenCL.dll`; otherwise assumes available if feature is enabled.

GPU layer offload:

- CPU backend uses `0` GPU layers.
- CUDA/Vulkan/OpenCL use `999` GPU layers.
- This is a coarse "offload all layers" setting, not a measured memory policy.

Offloading:

- MoE CPU offloading is configured on `LlamaEngine` through:
  - `with_moe_config(cpu_moe_all, n_cpu_moe)`
  - `model_params.with_n_cpu_moe(n)`
  - `model_params.with_cpu_moe_all()`
- These options are engine-level configuration, not request-level.

Context/thread/batch:

- `ctx_len` from `ModelSpec` becomes `with_n_ctx(...)`.
- Batch size is adaptive from context length, capped at `8192`.
- microbatch is fixed to `512`.
- threads use `spec.n_threads` or `get_optimal_thread_count()`.
- thread count is per loaded context/model load.

HuggingFace behavior:

- Uses hardcoded `C:/Python311/python.exe`.
- Load verifies Python imports and model load via subprocess.
- Generation runs a new Python subprocess with a script that loads tokenizer/model and then generates.
- Device is set to `"cpu"` in adapter-created `UniversalModelSpec`.
- `device_map="auto"` is used only if device equals `"cuda"`, which adapter does not set for this path.

MLX behavior:

- Feature-gated.
- Requires macOS Apple Silicon check.
- `MLXModel` implementation is placeholder text generation, not verified real MLX inference.

## Memory Behavior

Does each load duplicate model weights?

- For llama path, yes at Shimmy code level: each `LlamaEngine::load()` calls `LlamaModel::load_from_file(...)` and returns a new owned `LlamaLoaded`.
- Whether lower-level OS file cache or llama binding shares pages internally is not verified in inspected files.

Is memory shared between requests?

- Not at `InferenceEngineAdapter`/OpenAI path level.
- Loaded model objects are per request.

Is VRAM reused?

- Not verified in inspected files.
- Given per-request loads and no cache, the code does not explicitly reuse VRAM-resident loaded weights across requests.

Memory limit enforcement:

- Llama load catches errors containing `"failed to allocate"` or `"CPU_REPACK buffer"` and returns a detailed error.
- No proactive RAM/VRAM limit enforcement exists in inspected engine path.
- `SmartPreloader` evicts by count, not memory, and is not wired into OpenAI path.
- `ModelManager.max_memory_mb` is not enforced against actual memory usage in inspected code.

SafeTensors memory:

- Files >100MB use memory mapping when `use_mmap` is true.
- Smaller files are read into memory.
- Cache is disabled.
- Each load creates a new `SafeTensorsModel`.

## SafeTensors Behavior

Normal `.safetensors` model path:

- Adapter routes `.safetensors` to `SafeTensorsEngine`.
- `SafeTensorsEngine::load()` validates the file format.
- It loads via memory map for files over 100MB or reads into memory otherwise.
- It parses config from `config.json` if present, otherwise infers defaults from tensor names/shapes.
- It loads `tokenizer.json` if present, otherwise uses a simple character tokenizer.
- Generation is a placeholder/template response, not real transformer inference in inspected code.

SafeTensors LoRA with llama:

- If `LlamaEngine::load()` sees `spec.lora_path` ending in `.safetensors`, it returns an error instructing conversion to GGUF.
- It does not call `convert_safetensors_to_gguf()` automatically in inspected code.

`safetensors_adapter.rs`:

- Contains conversion helper `convert_safetensors_to_gguf`.
- It may shell out to `which` and `python`.
- `rg` found no production call sites in inspected files; references are module export and tests.
- Therefore automatic conversion during normal OpenAI request path is not verified in inspected files.

Failure modes:

- Not SafeTensors format.
- File read/metadata/open failure.
- SafeTensors deserialize failure.
- `config.json` parse failure.
- `tokenizer.json` parse failure.
- Conversion helper failures if explicitly called elsewhere.

## Failure Mode Mapping

| Category | Source location | Condition | Recoverability | Retry safety |
|---|---|---|---|---|
| `model_load_failed` | `InferenceEngineAdapter::load` backend routing | Backend selected but backend `load()` returns error | Depends on cause | Usually no unless transient filesystem/backend |
| `model_load_failed` | `LlamaEngine::load` | `LlamaModel::load_from_file(...)` fails for invalid/missing/corrupt GGUF | Fix model/path/config | No |
| `resource_exhausted` | `LlamaEngine::load` | Error contains `failed to allocate` or `CPU_REPACK buffer` | Requires smaller model, more RAM/VRAM, different backend/offload | No immediate retry |
| `model_load_failed` | `LlamaEngine::load` | `model.new_context(...)` fails | Depends on context/resources/model | Maybe after resource change |
| `model_load_failed` | `LlamaEngine::load` | SafeTensors LoRA supplied | Requires conversion to GGUF | No |
| `model_load_failed` | `LlamaEngine::load` | `lora_adapter_init` or `lora_adapter_set` fails | Fix adapter/path/compatibility | No |
| `generation_failed` | `LlamaLoaded::generate` | Tokenization fails | Prompt/model/tokenizer issue | Maybe with changed prompt/model |
| `generation_failed` | `LlamaLoaded::generate` | Context mutex poisoned/lock fails | Internal runtime error | Maybe after restart |
| `generation_failed` | `LlamaLoaded::generate` | `ctx.decode(...)`, batch add, sampling, or token conversion path fails | Backend/model/resource dependent | Maybe |
| `model_load_failed` | `SafeTensorsEngine::load` | Not SafeTensors format | Fix file | No |
| `model_load_failed` | `SafeTensorsEngine::load` | Metadata/read/mmap/deserialize/config/tokenizer failure | Fix file/config/tokenizer | No |
| `generation_failed` | `SafeTensorsModel::generate` | `simple_generate(...)` returns error | Not observed in normal placeholder path | Maybe |
| `backend_unavailable` | `HuggingFaceModel::load` | Hardcoded Python path missing or Python deps missing | Install/fix environment | No immediate retry |
| `model_load_failed` | `HuggingFaceModel::load` | Python can run but model load verification fails | Fix model/cache/deps | Maybe if transient |
| `generation_failed` | `HuggingFaceModel::generate` | Python generation subprocess exits non-zero | Backend/model/resource/deps dependent | Maybe |
| `backend_unavailable` | `MLXEngine::load` | MLX unavailable on system | Requires macOS Apple Silicon/feature/env | No |
| `model_load_failed` | `MLXModel::new` | Model file missing | Fix file/path | No |
| `timeout` | Engine path | No engine timeout found | NUCLEO-side only | Adapter policy |
| `unknown_backend_error` | Any backend | Any unclassified anyhow error | Unknown | Maybe |

## NUCLEO Risk Assessment

Safe concurrency level:

- **Unknown above 1.**
- Strict hardening posture should assume one in-flight generation per Shimmy instance or at least one in-flight generation per model.

Can caching be trusted?

- No.
- `InferenceEngineAdapter` explicitly has no active loaded-model cache.
- `ModelManager` and `SmartPreloader` are not used by OpenAI route in inspected files.

Must model loading be externally serialized?

- Yes, if NUCLEO wants deterministic memory behavior.
- Without serialization, concurrent requests can duplicate `LlamaModel::load_from_file(...)`.

Must NUCLEO enforce a per-model lock?

- Yes for a future strict adapter.
- A per-instance lock may be safer than per-model lock if the backend shares global GPU/CPU resources.

Treat every request as cold start?

- Yes, unless Phase 04 findings are superseded by inspecting a different production path.
- In the inspected OpenAI path, every request calls `engine.load(...)`.

Primary risks:

- Cold load on every request.
- Duplicate model memory under concurrency.
- Bare 502 hides internal cause.
- Streamed errors are swallowed, inherited from Phase 02.
- HuggingFace backend spawns Python and reloads model during generation.
- MLX implementation appears placeholder and should not be treated as production inference.

## Recommended Constraints for Adapter

Required adapter constraints:

- Use only `POST /v1/chat/completions` with `stream:false`.
- Enforce a NUCLEO model allowlist.
- Enforce strict request validation before sending to Shimmy.
- Enforce client-side connect/read/total timeout.
- Enforce at most one in-flight request per Shimmy instance until engine behavior is proven under load.
- Prefer process isolation for Shimmy.
- Treat 502 as ambiguous unless adapter has phase-specific instrumentation.
- Log route, model ID, backend instance, latency, HTTP status, mapped error, timeout flag, response validation result, and content length.

Resource constraints:

- Do not rely on Shimmy for memory limits.
- Do not rely on Shimmy for loaded-model eviction.
- Do not rely on Shimmy for token usage accounting.
- Do not enable streaming in hardening phase.
- Do not use HuggingFace backend unless Python subprocess behavior is explicitly accepted and isolated.
- Do not treat SafeTensors engine as real transformer inference based on inspected code; its generation path is placeholder.

Concurrency constraints:

- Serialize per model at minimum.
- Prefer global serialization per Shimmy process for llama backend until benchmarked.
- Use separate Shimmy processes for parallelism if required.
- Consider external process restart as the only reliable memory reset lever verified at this level.

## Final Classification (safe / risky / requires isolation)

Classification: **risky / requires isolation**

CRITICAL:

- No active model cache in `InferenceEngineAdapter`.
- OpenAI request path loads per request.
- Same model can be loaded concurrently by multiple requests.
- Llama loaded-model mutex protects only one loaded instance, not same-model concurrency across requests.
- No verified memory limit or VRAM reuse.
- Llama memory allocation failures collapse into HTTP 502 at API boundary.
- HuggingFace backend depends on hardcoded Python path and subprocess model loading.
- SafeTensors generation is placeholder, not verified real LLM inference.

INFORMATIVE:

- Llama backend uses global `OnceLock` only for llama.cpp backend initialization, not model caching.
- Llama context uses `Mutex` and unsafe `Send`/`Sync`.
- GPU backend selection is compile-feature and CLI dependent.
- GPU detection shells out to system tools for some backends.
- MoE CPU offload is engine-level.
- SafeTensors model files may use memory mapping above 100MB.

PREMATURE:

- Trusting `ModelManager` or `SmartPreloader` for production OpenAI route behavior.
- Using MLX as a production backend based on inspected code.
- Assuming HuggingFace backend is local-only deterministic inference.
- Supporting parallel requests without external serialization.
- Depending on Shimmy for memory lifecycle management.
