# llm_lab UI Interaction

## What This UI Is

`runtime_lab/llm_lab_ui` is a local laboratory interface for running and viewing `llm_lab` experiment artifacts.

It is a small FastAPI server plus a static HTML/JavaScript page.

It can:

- submit a prompt to the existing `llm_lab` experiment runner;
- choose mode: `mock`, `mock-success`, or `ollama`;
- pass local model roles for Ollama experiments;
- list artifact files from `runtime_lab/llm_lab/artifacts`;
- load one artifact JSON by experiment ID;
- render Stage 1 responses, Stage 2 reviews, aggregate rankings, Stage 3 synthesis, and explicit errors.

## What This UI Is Not

This UI is not a NUCLEO Runtime interface.

It does not:

- call `AgentService`;
- call Runtime or Orchestrator;
- call Planner;
- call PolicyEngine;
- call ToolRegistry;
- execute Tools;
- produce AgentResponse;
- make policy decisions;
- call external APIs;
- integrate Shimmy;
- integrate llm-council code directly.

## Relationship To llm_lab

The UI is a local wrapper around:

```text
runtime_lab/llm_lab/experiment_runner.py
runtime_lab/llm_lab/artifacts/{experiment_id}.json
runtime_lab/docs/llm_lab_experiment_artifact_contract.md
```

The backend imports the experiment runner directly and validates artifacts through the existing contract validator.

The UI does not define a second artifact format.

## Difference From NUCLEO Core

NUCLEO core remains the canonical application/runtime path.

The UI is outside that path:

```text
runtime_lab/llm_lab_ui -> runtime_lab/llm_lab -> artifact JSON
```

It is not part of:

```text
Request -> FastAPI -> AgentService -> Runtime/Orchestrator -> Planner -> PolicyEngine -> ToolRegistry -> Tool -> AgentResponse
```

## Start Backend And Frontend

The backend serves both API and the static frontend page.

From repository root:

```bash
.venv/bin/python -m uvicorn runtime_lab.llm_lab_ui.backend.main:app \
  --host 127.0.0.1 \
  --port 8765
```

Open:

```text
http://127.0.0.1:8765/
```

No separate frontend build step is required.

## Run Mock Experiment

In the UI:

1. Enter a prompt.
2. Select `mock`.
3. Click `Run`.

Behavior:

- runs a deterministic mock experiment with explicit errors;
- writes one artifact under `runtime_lab/llm_lab/artifacts`;
- renders failed model calls and malformed review/synthesis errors explicitly.

For a fully successful mock experiment:

1. Select `mock-success`.
2. Click `Run`.

## Run Ollama Experiment

Prerequisites:

- Ollama is running locally.
- The existing `llm_lab` local models are available.
- Confirm installed model names with:

```bash
ollama list
```

Use exact model names from `ollama list` when needed. Ollama commonly exposes
tagged names such as `mistral:latest`.

Known local model IDs accepted by the UI:

- `qwen`
- `qwen2.5-coder:7b`
- `mistral`
- `mistral:latest`
- `llama3.1`
- `llama3.1:8b`

In the UI:

1. Select `ollama`.
2. Set Stage 1 models, for example:

```text
qwen,mistral,llama3.1:8b
```

3. Set Stage 2 reviewers, for example:

```text
qwen,mistral,llama3.1:8b
```

4. Set chairman:

```text
qwen
```

5. Click `Run`.

## Using Multiple Local Models

The experiment runner treats all selected local models through the same
Ollama adapter path. No model is privileged by the artifact contract.

The UI accepts the same comma-separated model list:

```text
qwen,mistral,llama3.1:8b
```

Exact tagged names are also valid when they appear in `ollama list`, for
example:

```text
qwen2.5-coder:7b,mistral:latest,llama3.1:8b
```

Example:

```bash
python runtime_lab/llm_lab/experiment_runner.py \
  --mode ollama \
  --stage1-models qwen,mistral,llama3.1:8b \
  --stage2-reviewers qwen,mistral,llama3.1:8b \
  --chairman qwen \
  --input "Compare the role of deterministic artifacts in llm_lab."
```

Behavior:

- every Stage 1 model call is recorded;
- every Stage 2 reviewer call is recorded;
- failures are stored explicitly with `status=error`;
- empty output is not treated as success;
- malformed rankings are not treated as success.

## API Endpoints

```text
GET  /health
GET  /api/artifacts
GET  /api/artifacts/{experiment_id}
POST /api/experiments
```

`POST /api/experiments` body:

```json
{
  "mode": "mock",
  "input": "Compare local and remote inference.",
  "stage1_models": ["qwen", "mistral", "llama3.1:8b"],
  "stage2_reviewers": ["qwen", "mistral", "llama3.1:8b"],
  "chairman": "qwen"
}
```

Response:

```json
{
  "experiment_id": "...",
  "artifact_path": "runtime_lab/llm_lab/artifacts/....json",
  "status": "success"
}
```

## Artifact Storage

Artifacts are stored at:

```text
runtime_lab/llm_lab/artifacts/{experiment_id}.json
```

The UI only reads JSON files from this directory.

Temporary files ending in:

```text
.tmp.json
```

are ignored by list operations.

## Hard Boundaries

- No tools.
- No policy.
- No Runtime.
- No Planner.
- No AgentService.
- No AgentResponse.
- No external APIs.
- No arbitrary shell commands.
- No arbitrary file paths.
- No external repository modifications.

## Known Limitations

- No token streaming.
- No stage-level SSE.
- No authentication.
- No artifact deletion.
- No artifact editing.
- `mock` mode intentionally creates an artifact with explicit errors.
- `mock-success` creates a successful artifact.
- `ollama` mode is limited to the local model IDs explicitly allowed by
  `runtime_lab/llm_lab/model_adapter.py`.
- Ollama availability is not managed by the UI.
- Existing old artifacts that do not satisfy the current validator may fail to load.
