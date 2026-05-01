1. DIRECTORY STRUCTURE

```text
runtime_lab/llm_lab_ui/
├── backend/
│   └── main.py
└── frontend/
    └── index.html
```

- `backend/main.py`: FastAPI server. Serves the frontend, lists/reads experiment artifacts, creates experiments by calling `runtime_lab/llm_lab/experiment_runner.py`.
- `frontend/index.html`: single-page HTML/CSS/JS UI. Sends `fetch()` requests to the backend and renders experiment artifacts.

2. BACKEND CONTRACT

File: `runtime_lab/llm_lab_ui/backend/main.py`

Framework used:

- `FastAPI`
- `Pydantic`
- `CORSMiddleware`

Imports/dependencies:

```python
json
sys
Path
Literal
FastAPI
HTTPException
CORSMiddleware
FileResponse
BaseModel
Field
field_validator
```

Imports from `runtime_lab/llm_lab`:

```python
from experiment_runner import default_config, run_experiment
from experiment_validator import ArtifactValidationError, validate_artifact
from model_adapter import OLLAMA_MODEL_ALIASES
```

It imports `llm_lab` modules by inserting this path into `sys.path`:

```python
runtime_lab/llm_lab
```

It does not duplicate the full experiment runner, but it does duplicate/own some UI-specific routing decisions:

- allowed modes
- allowed local model set
- default model list
- mock model IDs for UI experiments
- artifact listing metadata shape

Endpoints:

```text
GET /
```

Response:

- Serves `runtime_lab/llm_lab_ui/frontend/index.html` via `FileResponse`.

```text
GET /health
```

Response schema:

```json
{
  "status": "ok",
  "service": "llm_lab_ui",
  "scope": "runtime_lab_only"
}
```

```text
GET /api/artifacts
```

Response schema:

```json
[
  {
    "experiment_id": "string",
    "created_at": "string or null",
    "completed_at": "string or null",
    "status": "string",
    "artifact_path": "string",
    "mode": "string or null",
    "input_preview": "string",
    "contract_valid": true
  }
]
```

For invalid artifact files, item shape becomes:

```json
{
  "experiment_id": "string",
  "created_at": "string or null",
  "completed_at": "string or null",
  "status": "contract_error",
  "artifact_path": "string",
  "mode": "string or null",
  "input_preview": "string",
  "contract_valid": false,
  "contract_error": "string"
}
```

```text
GET /api/artifacts/{experiment_id}
```

Behavior:

- Validates `experiment_id` as UUID.
- Reads `runtime_lab/llm_lab/artifacts/{experiment_id}.json`.
- Validates it with `validate_artifact()`.

Success response:

- Full artifact JSON.

Error responses:

- `400`: invalid UUID.
- `404`: artifact file not found.
- `500`: invalid JSON or artifact contract violation.

```text
POST /api/experiments
```

Request body schema:

```json
{
  "mode": "mock | mock-success | ollama",
  "input": "non-empty string",
  "stage1_models": ["string"],
  "stage2_reviewers": ["string"],
  "chairman": "string"
}
```

Defaults in backend model:

```json
{
  "stage1_models": ["qwen", "mistral", "llama3.1:8b"],
  "stage2_reviewers": ["qwen", "mistral", "llama3.1:8b"],
  "chairman": "qwen"
}
```

Success response:

```json
{
  "experiment_id": "string",
  "artifact_path": "string",
  "status": "success | partial_success | error"
}
```

Validation/error behavior:

- Invalid body: FastAPI/Pydantic validation error, normally `422`.
- Unsupported mode explicit check: `400`, although `Literal` already validates mode.
- Artifact validation failure after run: `500`.
- Other unhandled runtime errors: UNKNOWN exact response body.

CORS behavior:

```python
allow_origins=[
  "http://127.0.0.1:8765",
  "http://localhost:8765"
]
allow_credentials=False
allow_methods=["GET", "POST"]
allow_headers=["Content-Type"]
```

3. FRONTEND CONTRACT

File: `runtime_lab/llm_lab_ui/frontend/index.html`

UI inputs:

- `textarea#prompt`
  - default: `Compare local inference and remote inference for HARDENING.`
- `select#mode`
  - `mock`
  - `mock-success`
  - `ollama`
- `input#stage1`
  - default: `qwen,mistral,llama3.1:8b`
- `input#stage2`
  - default: `qwen,mistral,llama3.1:8b`
- `input#chairman`
  - default: `qwen`

Buttons/actions:

- `Run`: submits experiment form.
- `Refresh`: reloads artifact list.
- Artifact list item button: loads artifact detail.

API endpoints called:

```text
GET /api/artifacts
GET /api/artifacts/{experiment_id}
POST /api/experiments
```

Payload sent by `Run`:

```json
{
  "mode": "value from #mode",
  "input": "value from #prompt",
  "stage1_models": ["CSV from #stage1"],
  "stage2_reviewers": ["CSV from #stage2"],
  "chairman": "trimmed #chairman"
}
```

Response fields expected from `POST /api/experiments`:

```json
{
  "experiment_id": "string",
  "status": "string"
}
```

Response fields expected from artifact detail:

```json
{
  "status": "string",
  "experiment_id": "string",
  "created_at": "string",
  "completed_at": "string",
  "config": {"backend_profile": "string"},
  "input": {"user_input": "string"},
  "stage1_responses": [
    {
      "model_id": "string",
      "response": "string or null",
      "status": "success | error",
      "latency_ms": "number",
      "error_type": "string or null",
      "error_message": "string or null"
    }
  ],
  "stage2_reviews": [
    {
      "reviewer_model_id": "string",
      "raw_review_text": "string or null",
      "parsed_ranking": ["string"],
      "status": "success | error",
      "latency_ms": "number",
      "error_type": "string or null",
      "error_message": "string or null"
    }
  ],
  "aggregate_rankings": [
    {
      "model_id": "string",
      "average_rank": "number or null",
      "rankings_count": "number",
      "valid": "boolean"
    }
  ],
  "stage3_synthesis": {
    "model_id": "string",
    "response": "string or null",
    "status": "success | error",
    "latency_ms": "number",
    "error_type": "string or null",
    "error_message": "string or null"
  }
}
```

Rendering behavior:

- Artifact list renders status, experiment ID, created date, input preview.
- Invalid contract artifacts are shown disabled.
- Artifact detail renders summary, Stage 1 cards, Stage 2 cards, aggregate rankings table, Stage 3 card.
- Error stage records render `error_type: error_message`.
- Successful stage records render response text.
- HTML escaping is performed before injecting values.

Error handling behavior:

- Failed `fetch()` responses throw `Error(await res.text())`.
- Run errors appear in `#run-message`.
- Artifact load errors appear in `#artifact-summary`.
- Initial artifact list load errors render an error panel in the artifact list.

4. END-TO-END FLOW

```text
browser
→ GET /
→ backend returns frontend/index.html
→ frontend runs refreshArtifacts()
→ GET /api/artifacts
→ backend reads runtime_lab/llm_lab/artifacts/*.json
→ backend validates each artifact
→ frontend renders artifact list
```

Run flow:

```text
browser form submit
→ frontend builds JSON payload
→ POST /api/experiments
→ backend validates ExperimentRequest
→ backend chooses mode
→ backend calls llm_lab experiment_runner.run_experiment()
→ experiment_runner calls model_adapter.call_model()
→ mock mode: model_adapter returns deterministic mock output
→ ollama mode: model_adapter calls local Ollama
→ experiment_runner builds and validates artifact
→ artifact written under runtime_lab/llm_lab/artifacts/
→ backend reads artifact back
→ backend returns experiment_id, artifact_path, status
→ frontend calls GET /api/artifacts/{experiment_id}
→ backend returns full artifact
→ frontend renders stages and rankings
```

5. MODEL SELECTION FLOW

- EXPLICIT: Frontend provides editable text inputs for Stage 1 models, Stage 2 reviewers, and chairman.
- EXPLICIT: Frontend converts Stage 1 and Stage 2 comma-separated strings into arrays.
- EXPLICIT: Frontend sends those arrays in `POST /api/experiments`.
- EXPLICIT: Backend validates model names against `ALLOWED_LOCAL_MODELS`.
- EXPLICIT: `ALLOWED_LOCAL_MODELS` is derived from `model_adapter.OLLAMA_MODEL_ALIASES`.
- EXPLICIT: Currently allowed model keys are:
  ```text
  qwen
  qwen2.5-coder:7b
  mistral
  mistral:latest
  llama3.1
  llama3.1:8b
  ```
- EXPLICIT: For `mode="mock"` and `mode="mock-success"`, frontend model fields are ignored; backend uses hardcoded mock model lists.
- EXPLICIT: For `mode="ollama"`, backend passes request model lists and chairman into `run_experiment()`.
- EXPLICIT: `run_experiment()` passes each model ID into `model_adapter.call_model()`.
- EXPLICIT: `model_adapter` resolves aliases using installed Ollama models from `/api/tags`.
- EXPLICIT: The final execution target is local Ollama `/api/chat`.
- INFERRED: The UI assumes all accepted non-mock model names are local Ollama-compatible names.

6. ARTIFACT / REPORT FLOW

The UI does create experiment artifacts:

- `POST /api/experiments`
- backend calls `run_experiment()`
- artifact is written under:
  ```text
  runtime_lab/llm_lab/artifacts/{experiment_id}.json
  ```

The UI reads artifacts:

- `GET /api/artifacts`
- `GET /api/artifacts/{experiment_id}`

The UI does not write reports.

The UI does not call:

```text
runtime_lab/llm_lab/nucleo_state_review.py
runtime_lab/llm_lab/reports/
```

The UI does not only display transient responses. It displays persisted artifact data after the backend writes and rereads the artifact.

7. CONTRACTS

Frontend → Backend, create experiment:

```json
{
  "mode": "mock | mock-success | ollama",
  "input": "non-empty string",
  "stage1_models": ["qwen", "mistral", "llama3.1:8b"],
  "stage2_reviewers": ["qwen", "mistral", "llama3.1:8b"],
  "chairman": "qwen"
}
```

Backend → Frontend, create response:

```json
{
  "experiment_id": "uuid",
  "artifact_path": "runtime_lab/llm_lab/artifacts/{uuid}.json",
  "status": "success | partial_success | error"
}
```

Frontend → Backend, list artifacts:

```text
GET /api/artifacts
```

Backend → Frontend, list artifacts:

```json
[
  {
    "experiment_id": "uuid",
    "created_at": "timestamp",
    "completed_at": "timestamp",
    "status": "string",
    "artifact_path": "string",
    "mode": "string",
    "input_preview": "string",
    "contract_valid": true
  }
]
```

Backend → `llm_lab`:

```python
run_experiment(
    user_input=request.input,
    stage1_responders=[...],
    stage2_reviewers=[...],
    stage3_chairman="...",
    adapter_mode="mock_success | mock_errors | ollama",
    config=default_config(..., 120000),
    notes="..."
)
```

Backend → `llm_lab` validation:

```python
validate_artifact(artifact)
```

Backend/Ollama:

The backend does not call Ollama directly. Ollama is called by `runtime_lab/llm_lab/model_adapter.py`.

Ollama tags request:

```text
GET http://localhost:11434/api/tags
```

Expected response shape:

```json
{
  "models": [
    {"name": "model-name"}
  ]
}
```

Ollama chat request:

```json
{
  "model": "resolved_model_name",
  "messages": [
    {
      "role": "system",
      "content": "You are running inside runtime_lab/llm_lab..."
    },
    {
      "role": "user",
      "content": "experiment prompt"
    }
  ],
  "stream": false
}
```

Expected response shape:

```json
{
  "message": {
    "content": "string"
  }
}
```

8. COUPLING RISKS

- MEDIUM: Backend computes repo paths with `Path(__file__).resolve().parents[3]`; moving the file changes path resolution.
- HIGH: Backend mutates `sys.path` to import `experiment_runner`, `experiment_validator`, and `model_adapter` by bare module name.
- HIGH: Backend directly depends on `run_experiment()` signature.
- MEDIUM: Backend hardcodes `runtime_lab/llm_lab/artifacts` as the artifact directory.
- HIGH: Frontend expects the current artifact schema field names exactly: `stage1_responses`, `stage2_reviews`, `aggregate_rankings`, `stage3_synthesis`.
- MEDIUM: Backend artifact list expects `config.backend_profile` and `input.user_input`.
- MEDIUM: Frontend default model strings are hardcoded independently from backend defaults.
- MEDIUM: Backend hardcodes UI mock model IDs separately from `experiment_runner.py` mock constants.
- HIGH: Backend allowed model names are coupled to `model_adapter.OLLAMA_MODEL_ALIASES`.
- HIGH: Current non-mock execution is coupled to Ollama through `adapter_mode="ollama"`.
- MEDIUM: Backend always uses `default_config(..., 120000)`; timeout is not part of frontend contract.
- LOW: CORS is coupled to `http://127.0.0.1:8765` and `http://localhost:8765`.
- MEDIUM: Invalid artifacts are included in the list but disabled in the frontend, so artifact contract validity controls UI navigation.
- LOW: UI header says “no external APIs”; current code path uses local Ollama only.

9. REMOTE LLM READINESS

Can remote models be added through existing `model_adapter.py` without changing frontend?

- Partly.
- The frontend already sends free-text model names as arrays, so it does not require a fixed model dropdown.
- But the frontend mode selector only exposes `mock`, `mock-success`, and `ollama`.
- If remote execution reused the existing `ollama` mode name and backend contract, frontend could remain unchanged.
- If remote execution needs a new mode, frontend would need a mode option change.

Can remote models be added without changing backend?

- No, not with current behavior.
- Backend validates model names against `ALLOWED_LOCAL_MODELS`, derived from `OLLAMA_MODEL_ALIASES`.
- Backend hardcodes `adapter_mode="ollama"` for real model execution.
- Backend request type only allows `mode: "mock" | "mock-success" | "ollama"`.

Files that would probably need changes:

```text
runtime_lab/llm_lab/model_adapter.py
runtime_lab/llm_lab_ui/backend/main.py
runtime_lab/llm_lab/experiment_runner.py
runtime_lab/llm_lab_ui/frontend/index.html
```

`frontend/index.html` is only probably needed if remote models require visible new mode/defaults.

Current behavior that must not be broken:

- `GET /`
- `GET /health`
- `GET /api/artifacts`
- `GET /api/artifacts/{experiment_id}`
- `POST /api/experiments`
- existing request JSON shape
- existing artifact schema rendering
- mock and mock-success modes
- local Ollama mode
- artifact validation before display
- artifact writing under `runtime_lab/llm_lab/artifacts`
- default local model names: `qwen`, `mistral`, `llama3.1:8b`

END.