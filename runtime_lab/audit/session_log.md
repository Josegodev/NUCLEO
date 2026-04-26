# Runtime Lab Audit Session Log

### Session: llm_lab + Shimmy + Council Hardening

Date: 2026-04-26

Scope:

- `runtime_lab/audit/`
- `runtime_lab/docs/`
- `runtime_lab/llm_lab/`
- `runtime_lab/llm_lab_ui/`
- external reference repositories inspected read-only

NUCLEO core status:

- Core runtime logic was not modified by this session.
- `AgentService`, Runtime/Orchestrator, Planner, PolicyEngine, ToolRegistry,
  Tools, and AgentResponse remain outside the llm_lab path.

#### Shimmy Audit

Completed audit phases:

- Phase 01: entrypoints
- Phase 02: API surface and error mapping
- Phase 03: model runtime and resources
- Phase 04: engine, concurrency, and memory
- Phase 05: licensing and external dependencies

Key findings:

- OpenAI-compatible text route is the only plausible future adapter boundary.
- Loaded model caching is not active in the inspected OpenAI path.
- Text generation path performs request-time model loading.
- Concurrent same-model requests can duplicate load and memory pressure.
- Streaming behavior is not safe for HARDENING because errors can be hidden.
- Error envelopes are inconsistent; multiple failures collapse to bare `502`.
- Vision licensing is isolated from inspected text inference paths.
- Vision/Keygen/Stripe surfaces are not acceptable for NUCLEO inference use.

Decision:

- Shimmy remains an external inference backend candidate only.
- It is not integrated into NUCLEO core.
- Any future evaluation must use a strict adapter boundary and NUCLEO-owned
  validation/error normalization.

#### llm-council Audit

Key findings:

- Multi-stage orchestration pattern is useful for experiments:
  - Stage 1 raw responses
  - Stage 2 peer review/ranking
  - Stage 3 synthesis
- Async fan-out, response collection, ranking, synthesis, and artifact display
  are useful as lab concepts.
- Provider dependency and implementation style are not suitable for NUCLEO core.
- Broad exception-to-null behavior is not acceptable for HARDENING contracts.

Decision:

- llm-council is a reference pattern for `llm_lab` only.
- OpenRouter and external-provider behavior are not introduced into NUCLEO.
- No llm-council code is integrated directly.

#### llm_lab Implemented

Implemented or hardened:

- `runtime_lab/docs/llm_lab_experiment_artifact_contract.md`
- `runtime_lab/llm_lab/experiment_artifact.py`
- `runtime_lab/llm_lab/experiment_validator.py`
- `runtime_lab/llm_lab/model_adapter.py`
- `runtime_lab/llm_lab/experiment_runner.py`
- `runtime_lab/llm_lab_ui/backend/main.py`
- `runtime_lab/llm_lab_ui/frontend/index.html`
- `runtime_lab/docs/llm_lab_ui_interaction.md`

Behavior:

- deterministic sequential execution
- mock mode
- mock-success mode
- optional local Ollama mode for `qwen` and `mistral`
- one JSON artifact per experiment
- atomic artifact write via temporary file and rename
- strict artifact validation
- explicit errors for failed calls
- no silent model drops
- no external APIs

#### Key System Insight

Models are stateless from the system perspective.

Artifacts are system memory.

The durable state that matters for HARDENING is not a model's internal context;
it is the validated, versioned, auditable artifact stored by `llm_lab`.

#### Hardening Decisions

- Do not modify `run_mistral.py` or `run_qwen.py`.
- Keep local model chat scripts as separate lab utilities.
- Keep experiment execution deterministic and sequential.
- Use strict artifact contracts.
- Use closed error taxonomy.
- Do not use external APIs.
- Do not implement token streaming.
- Do not connect llm_lab to Runtime, Planner, PolicyEngine, ToolRegistry, Tools,
  or AgentResponse.
- Keep llm_lab UI as a local inspection layer only.

#### Current State

- `llm_lab` is stable enough for local validation.
- `llm_lab` is not integrated into NUCLEO core.
- Generated artifacts are ignored by Git except `.gitkeep`.
- External repositories remain research inputs only.
- Next validation step is to run mock, mock-success, and optional Ollama
  experiments and inspect resulting artifacts through the UI.
