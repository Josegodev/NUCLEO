DIRECTORY STRUCTURE
Scope note: ./llm_lab does not exist at repo root. Existing audited path is runtime_lab/llm_lab. No files were modified.

runtime_lab/llm_lab/
├── .codex
├── README.md
├── requirements.txt
├── run_mistral.py
├── run_qwen.py
├── experiment_runner.py
├── experiment_validator.py
├── experiment_artifact.py
├── model_adapter.py
├── nucleo_state_review.py
├── artifacts/
│   ├── .gitkeep
│   └── *.json
├── mistral/
│   ├── .codex
│   ├── IMPLEMENTACION.md
│   ├── chat_mistral_sqlite.py
│   ├── contexto.txt
│   ├── memoria.db
│   └── mistral_memory.py
├── qwen/
│   ├── .codex
│   ├── IMPLEMENTACION.md
│   ├── chat_qwen_sqlite.py
│   ├── contexto.txt
│   ├── memoria.db
│   ├── memoria_qwen.db
│   └── qwen_memory.py
└── reports/
    └── nucleo_state_review_*.md
README.md: documenta que llm_lab es lateral, experimental y no integrado en Runtime, Planner, PolicyEngine, ToolRegistry ni Tools.
requirements.txt: solo declara requests==2.33.1.
run_mistral.py: wrapper que llama a mistral.chat_mistral_sqlite.main.
run_qwen.py: wrapper que llama a qwen.chat_qwen_sqlite.main.
experiment_runner.py: ejecuta experimentos multi-modelo y escribe artefactos JSON.
experiment_validator.py: validador estricto del contrato de artefacto.
experiment_artifact.py: helpers para construir registros, rankings, artefactos y escritura atómica.
model_adapter.py: adaptador mock/Ollama para llamadas de modelo usadas por experiment_runner.py.
nucleo_state_review.py: genera informes Markdown de revisión HARDENING; su llamada LLM es un stub.
artifacts/: contiene artefactos JSON versionados por UUID.
mistral/: chat interactivo Mistral con SQLite local.
qwen/: chat interactivo Qwen con SQLite local.
reports/: informes Markdown generados por nucleo_state_review.py.
.codex: archivos vacíos.
EXECUTION FLOW

run_mistral.py

run_mistral.py
└── imports main from mistral/chat_mistral_sqlite.py
    └── main()
        ├── init_db()
        ├── input loop
        └── ask(text)
            ├── load_user_context()
            ├── get_messages(limit=20)
            ├── build_prompt(user_context, history, user_input)
            ├── requests.post(http://localhost:11434/api/chat)
            ├── response.raise_for_status()
            ├── extract_answer(response)
            ├── save_message("user", text)
            ├── save_message("assistant", answer)
            └── return answer

run_qwen.py

run_qwen.py
└── imports main from qwen/chat_qwen_sqlite.py
    └── main()
        ├── init_db()
        ├── input loop
        └── ask(text)
            ├── load_user_context()
            ├── get_messages(limit=20)
            ├── build_prompt(user_context, history, user_input)
            ├── requests.post(http://localhost:11434/api/chat)
            ├── response.raise_for_status()
            ├── extract_answer(response)
            ├── save_message("user", text)
            ├── save_message("assistant", answer)
            └── return answer
experiment_runner.py

experiment_runner.py
└── main()
    ├── argparse parses --input, --mode, models, chairman, timeout
    ├── safe_run(...)
    └── run_experiment(...)
        ├── new_experiment_id()
        ├── utc_now()
        ├── Stage 1:
        │   └── _stage1_call()
        │       └── model_adapter.call_model()
        ├── make_label_to_model()
        ├── Stage 2:
        │   └── _stage2_call()
        │       ├── build_review_prompt()
        │       ├── model_adapter.call_model()
        │       └── parse_ranking()
        ├── calculate_aggregate_rankings()
        ├── Stage 3:
        │   └── _stage3_call()
        │       ├── build_synthesis_prompt()
        │       └── model_adapter.call_model()
        ├── build_artifact()
        ├── validate_artifact()
        └── write_artifact_atomic()
            ├── validate_artifact()
            ├── write tmp JSON
            ├── validate tmp JSON
            └── os.replace(tmp, final)
Modes:

mock: writes two artifacts: one success, one error scenario.
mock-success: writes one success artifact.
mock-errors: writes one error-oriented artifact.
ollama: calls local Ollama through model_adapter.py.

CORE COMPONENTS
experiment_runner.py

Purpose: orchestrates a 3-stage experiment: responders, reviewers, chairman synthesis.
Main input contract:
run_experiment(
    *,
    user_input: str,
    stage1_responders: list[str],
    stage2_reviewers: list[str],
    stage3_chairman: str,
    adapter_mode: AdapterMode,
    config: dict[str, Any],
    notes: str | None = None,
) -> Path
Expected data:
user_input: non-empty string, validated later in artifact validation.
stage1_responders: non-empty unique model IDs.
stage2_reviewers: non-empty unique model IDs.
stage3_chairman: non-empty string.
adapter_mode: "mock_success", "mock_errors", or "ollama".
config: expected to contain at least timeout_ms; default config also has temperature, top_p, max_tokens, seed, backend_profile, prompt_template.
Output contract: returns Path to written artifact JSON.
Dependencies: argparse, sys, time, Path, experiment_artifact, experiment_validator, model_adapter.
experiment_validator.py

Purpose: validates artifact structure and consistency without mutation.
Main input contract:
validate_artifact(artifact: dict[str, Any]) -> None
Output contract:
returns None if valid.
raises ArtifactValidationError if invalid.
Dependencies: datetime, uuid, constants and calculate_aggregate_rankings from experiment_artifact.
model_adapter.py

Purpose: normalizes model calls for mock modes and local Ollama.
Main input contract:
call_model(model_id: str, prompt: str, *, mode: AdapterMode, timeout_ms: int) -> ModelCall
Output contract:
ModelCall(
    model_id: str,
    status: str,
    output: str | None,
    error_type: str | None,
    error_message: str | None,
    latency_ms: float,
)
Dependencies: requests, time, dataclass, Literal.
Adapter modes: "mock_success", "mock_errors", "ollama".
experiment_artifact.py

Purpose: builds artifact records, parses rankings, calculates aggregate rankings, determines experiment status, writes JSON atomically.
Main outputs:
success_record(...) -> dict[str, Any]
error_record(...) -> dict[str, Any]
make_label_to_model(...) -> dict[str, str]
parse_ranking(...) -> tuple[list[str], str | None]
calculate_aggregate_rankings(...) -> list[dict[str, Any]]
build_artifact(...) -> dict[str, Any]
write_artifact_atomic(...) -> Path
Dependencies: json, os, re, uuid, datetime, Path, Any, and dynamic import of experiment_validator.validate_artifact.
MODEL INTEGRATION
mistral/

Entry points:
external: runtime_lab/llm_lab/run_mistral.py
internal: runtime_lab/llm_lab/mistral/chat_mistral_sqlite.py
Model constant: MODEL = "mistral".
Ollama endpoint: http://localhost:11434/api/chat.
Input to Ollama:
{
  "model": "mistral",
  "messages": [
    {"role": "system", "content": "...SYSTEM CONTEXT + SYSTEM RULES..."},
    {"role": "user|assistant", "content": "...history..."},
    {"role": "user", "content": "...current user input..."}
  ],
  "stream": false
}
Expected Ollama output:
{
  "message": {
    "content": "assistant text"
  }
}
Stored output: two SQLite rows after successful response: user and assistant.
qwen/

Entry points:
external: runtime_lab/llm_lab/run_qwen.py
internal: runtime_lab/llm_lab/qwen/chat_qwen_sqlite.py
Model constant: MODEL = "qwen2.5-coder:7b".
Active DB path in current code: runtime_lab/llm_lab/qwen/memoria_qwen.db.
Same Ollama request/response contract as Mistral.
model_adapter.py Ollama integration

First calls GET http://localhost:11434/api/tags.
Resolves aliases:
qwen -> qwen2.5-coder:7b
mistral -> mistral:latest or mistral
llama3.1 -> llama3.1:8b
Then calls POST http://localhost:11434/api/chat with:
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
DATA FLOW
Interactive chat flow:

stdin prompt
→ main input loop
→ ask(text)
→ contexto.txt
→ SQLite history
→ build_prompt()
→ Ollama /api/chat
→ extract_answer()
→ SQLite mensajes table
→ printed answer
Experiment flow:

CLI --input
→ run_experiment(user_input)
→ Stage 1: raw user_input sent to responder models
→ stage1_responses records
→ label_to_model anonymizes successful responses as Response A/B/C
→ Stage 2: review prompt sent to reviewer models
→ parse_ranking validates labels
→ aggregate_rankings calculated
→ Stage 3: synthesis prompt sent to chairman model
→ build_artifact()
→ validate_artifact()
→ artifacts/{experiment_id}.json
Storage:

Chat memory:
Mistral: runtime_lab/llm_lab/mistral/memoria.db
Qwen: runtime_lab/llm_lab/qwen/memoria_qwen.db
Experiment artifacts:
runtime_lab/llm_lab/artifacts/{experiment_id}.json
Review reports:
runtime_lab/llm_lab/reports/nucleo_state_review_YYYYMMDD_HHMM.md
CONTRACTS (CRITICAL)
Artifact top-level structure:

{
  "schema_version": "llm_lab.experiment.v1",
  "experiment_id": "uuid",
  "created_at": "ISO-8601 timestamp with timezone",
  "completed_at": "ISO-8601 timestamp with timezone",
  "status": "success|partial_success|error",
  "input": {"user_input": "non-empty string"},
  "models": {
    "stage1_responders": ["model_id"],
    "stage2_reviewers": ["model_id"],
    "stage3_chairman": "model_id"
  },
  "config": {
    "temperature": 0.2,
    "top_p": 0.9,
    "max_tokens": 1024,
    "seed": null,
    "timeout_ms": 120000,
    "backend_profile": "mock_success|mock_errors|ollama",
    "prompt_template": "llm_lab.council.v1"
  },
  "stage1_responses": [],
  "label_to_model": {},
  "stage2_reviews": [],
  "aggregate_rankings": [],
  "stage3_synthesis": {},
  "metadata": {},
  "notes": "optional"
}
Stage 1 success:

{
  "model_id": "model",
  "status": "success",
  "response": "non-empty string",
  "error_type": null,
  "error_message": null,
  "latency_ms": 1.23,
  "timestamp": "ISO-8601 timestamp",
  "tokens_used": {"trusted": false}
}
Stage 1 error:

{
  "model_id": "model",
  "status": "error",
  "response": null,
  "error_type": "invalid_request|model_not_available|timeout|generation_failed|malformed_response|unsupported_feature|unknown_error",
  "error_message": "non-empty string",
  "latency_ms": 1.23,
  "timestamp": "ISO-8601 timestamp"
}
Stage 2 success:

{
  "reviewer_model_id": "model",
  "reviewed_labels": {"Response A": "model_id"},
  "status": "success",
  "raw_review_text": "non-empty string",
  "parsed_ranking": ["Response A", "Response B"],
  "error_type": null,
  "error_message": null,
  "latency_ms": 1.23,
  "timestamp": "ISO-8601 timestamp"
}
Stage 3 success:

{
  "model_id": "chairman",
  "status": "success",
  "response": "non-empty string",
  "error_type": null,
  "error_message": null,
  "latency_ms": 1.23,
  "timestamp": "ISO-8601 timestamp"
}
Validation rules:

Required top-level fields must exist.
schema_version must equal llm_lab.experiment.v1.
experiment_id must be UUID.
timestamps must be ISO-8601 and timezone-aware.
model lists must be non-empty, unique string lists.
timeout_ms must be positive integer.
temperature and top_p must be number or null.
max_tokens and seed must be integer or null.
Stage 1 must contain one record per responder.
Stage 2 must contain one record per reviewer.
label_to_model must contain exactly successful Stage 1 models.
labels must be deterministic: Response A, Response B, etc.
successful Stage 2 rankings must include every label exactly once.
failed Stage 2 rankings must be [].
aggregate_rankings must be reproducible from Stage 2.
Stage 3 model must match configured chairman.
global status is derived:
Stage 3 error -> error
any Stage 1 or Stage 2 error -> partial_success
otherwise -> success
Ranking parser contract:

Looks for labels matching regex Response [A-Z].
If text contains FINAL RANKING:, it parses only text after first occurrence.
If not, it parses the full text.
Unknown labels, duplicate labels, missing labels, or incomplete counts produce malformed ranking.
INFERRED:

Chat DB history records are expected to be shaped like:
{"role": "user|assistant", "content": "text"}
The table only enforces TEXT NOT NULL; allowed role values are not enforced by SQLite schema.
EXAMPLE EXECUTION
Real existing artifact inspected, not executed during this audit:

File: runtime_lab/llm_lab/artifacts/d23bab88-6c07-413c-b2fd-20d5fc5aa5d8.json
Mode: ollama
Input prompt:
¿RECUERDAS LAS ULTIMAS CONVERSACIONES?
Intermediate steps:

Stage 1 responders:
- qwen -> success
- mistral -> success
- llama3.1:8b -> success

label_to_model:
- Response A -> qwen
- Response B -> mistral
- Response C -> llama3.1:8b

Stage 2 reviewers:
- qwen -> success, ranking A/B/C
- mistral -> error, malformed_response
- llama3.1:8b -> success, ranking A/C/B

aggregate_rankings:
- qwen average_rank 1.0
- llama3.1:8b average_rank 2.5
- mistral average_rank 2.5

Stage 3 chairman:
- qwen -> success
Final output structure:

{
  "schema_version": "llm_lab.experiment.v1",
  "experiment_id": "d23bab88-6c07-413c-b2fd-20d5fc5aa5d8",
  "status": "partial_success",
  "input": {"user_input": "¿RECUERDAS LAS ULTIMAS CONVERSACIONES?"},
  "models": {
    "stage1_responders": ["qwen", "mistral", "llama3.1:8b"],
    "stage2_reviewers": ["qwen", "mistral", "llama3.1:8b"],
    "stage3_chairman": "qwen"
  },
  "stage1_responses": ["3 success records"],
  "label_to_model": {
    "Response A": "qwen",
    "Response B": "mistral",
    "Response C": "llama3.1:8b"
  },
  "stage2_reviews": ["2 success records", "1 malformed_response error record"],
  "aggregate_rankings": ["3 aggregate records"],
  "stage3_synthesis": "success record",
  "metadata": {
    "total_latency_ms": 10208.202,
    "runtime_profile": "ollama"
  }
}
RISKS / UNCERTAINTIES
LOW RISK: requested scope says ./llm_lab, but actual directory is runtime_lab/llm_lab. ./llm_lab at repo root is UNKNOWN.
HIGH RISK: artifact config records temperature, top_p, max_tokens, and seed, but model_adapter.py only passes model, messages, and stream to Ollama. Only timeout_ms affects the actual call path.
HIGH RISK: run_experiment() uses config["timeout_ms"] before artifact validation. Missing or invalid config can fail outside the artifact validation contract.
MEDIUM RISK: experiment_artifact.py contains a validate_artifact() wrapper that returns after delegating to experiment_validator; older validation code exists below that return and is unreachable.
MEDIUM RISK: ranking parsing is regex-based over Response [A-Z]; explanatory text containing repeated labels can make a review malformed, as seen in an existing artifact.
MEDIUM RISK: chat integrations validate that message.content is a string, but do not reject an empty string. The experiment adapter does reject empty output.
MEDIUM RISK: Qwen folder contains both memoria.db and memoria_qwen.db; current Qwen code uses memoria_qwen.db. The purpose of qwen/memoria.db is UNKNOWN.
MEDIUM RISK: SQLite schema accepts any role string. Current code writes user and assistant, but the database contract itself does not enforce those values.
LOW RISK: metadata.environment_snapshot.host_id is hardcoded as "requires definition" in generated artifacts.
LOW RISK: nucleo_state_review.py has call_local_llm() as a stub. It prepares reports but does not invoke a model.
END.