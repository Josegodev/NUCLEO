# NUCLEO llm_lab Experiment Artifact Contract

## Status

Scope: `runtime_lab/llm_lab` only.

This contract defines a deterministic artifact format for storing multi-model LLM experiments.

This contract is not part of NUCLEO core. It must not affect:

- `AgentService`
- `Runtime`
- `Planner`
- `PolicyEngine`
- `ToolRegistry`
- `Tool`
- `AgentResponse`

## Goals

- Store multi-model LLM experiments with full traceability.
- Preserve every attempted model call, including failures.
- Use a stable, versioned, auditable JSON structure.
- Avoid dependency on any external provider response schema.
- Use one closed error taxonomy across all experiment stages.
- Make aggregate rankings reproducible from stored review records.
- Support optional streaming/event logs without making them authoritative.

## Non-Goals

- This contract is not a NUCLEO Runtime contract.
- This contract does not define policy decisions.
- This contract does not define tool execution.
- This contract does not define backend integration behavior.
- This contract does not assume any specific LLM backend.
- This contract does not assume any external API schema.
- This contract does not define safety, trust, authorization, or routing policy.

## Canonical Artifact Shape

The canonical persisted artifact is one JSON object per experiment.

Required top-level fields:

- `schema_version`
- `experiment_id`
- `created_at`
- `input`
- `models`
- `config`
- `stage1_responses`
- `label_to_model`
- `stage2_reviews`
- `aggregate_rankings`
- `stage3_synthesis`
- `metadata`

Optional top-level fields:

- `notes`

## Full JSON Schema Example

This is a contract example, not executable JSON Schema syntax.

```json
{
  "schema_version": "llm_lab.experiment.v1",
  "experiment_id": "00000000-0000-4000-8000-000000000000",
  "created_at": "2026-04-26T12:00:00Z",
  "input": {
    "user_input": "Explain the tradeoffs of local model inference."
  },
  "models": [
    "local/model-a",
    "local/model-b",
    "local/model-c"
  ],
  "config": {
    "temperature": 0.2,
    "top_p": 0.9,
    "max_tokens": 1024,
    "seed": 12345,
    "timeout_ms": 120000,
    "backend_profile": "requires definition",
    "prompt_template": "requires definition"
  },
  "stage1_responses": [
    {
      "model_id": "local/model-a",
      "status": "success",
      "response": "Raw model response text.",
      "error_type": null,
      "error_message": null,
      "latency_ms": 1532,
      "tokens_used": {
        "prompt_tokens": 100,
        "completion_tokens": 220,
        "total_tokens": 320,
        "trusted": false
      },
      "timestamp": "2026-04-26T12:00:03Z"
    }
  ],
  "label_to_model": {
    "Response A": "local/model-a",
    "Response B": "local/model-b",
    "Response C": "local/model-c"
  },
  "stage2_reviews": [
    {
      "reviewer_model_id": "local/model-a",
      "reviewed_labels": {
        "Response A": "local/model-a",
        "Response B": "local/model-b",
        "Response C": "local/model-c"
      },
      "status": "success",
      "raw_review_text": "Review text including final ranking.",
      "parsed_ranking": [
        "Response B",
        "Response A",
        "Response C"
      ],
      "error_type": null,
      "error_message": null,
      "latency_ms": 2410,
      "timestamp": "2026-04-26T12:00:07Z"
    }
  ],
  "aggregate_rankings": [
    {
      "model_id": "local/model-b",
      "average_rank": 1.33,
      "rankings_count": 3,
      "valid": true
    }
  ],
  "stage3_synthesis": {
    "model_id": "local/model-chairman",
    "status": "success",
    "response": "Final synthesized answer.",
    "error_type": null,
    "error_message": null,
    "latency_ms": 3012,
    "timestamp": "2026-04-26T12:00:12Z"
  },
  "metadata": {
    "total_latency_ms": 12000,
    "per_stage_latency": {
      "stage1_ms": 2000,
      "stage2_ms": 5000,
      "stage3_ms": 3012
    },
    "environment_snapshot": {
      "llm_lab_version": "requires definition",
      "host_id": "requires definition",
      "runtime_profile": "requires definition"
    }
  },
  "notes": "Optional human-authored note."
}
```

## Field Definitions

### `schema_version`

Required string.

Current value:

```json
"llm_lab.experiment.v1"
```

Validation:

- Must be present.
- Must be a non-empty string.
- Consumers must reject unknown versions unless they explicitly support migration.

### `experiment_id`

Required UUID string.

Validation:

- Must be valid UUID format.
- Must identify exactly one experiment artifact.

### `created_at`

Required ISO 8601 timestamp string.

Validation:

- Must include timezone or use `Z`.
- Must represent artifact creation time, not completion time.

### `input`

Required object.

Shape:

```json
{
  "user_input": "string"
}
```

Validation:

- `user_input` is required.
- `user_input` must be a string.
- Empty string is invalid.

### `models`

Required array of strings.

Meaning:

- Ordered list of model identifiers selected for Stage 1 response generation.

Validation:

- Must contain at least one model ID.
- Each item must be a non-empty string.
- IDs must be unique.
- Every model attempted in Stage 1 must appear here.
- Every successful or failed Stage 1 record must reference an ID from this list.

### `config`

Required object.

Purpose:

- Snapshot of generation and experiment parameters at execution time.
- Must be sufficient to understand the intended run configuration.
- Does not need to guarantee bit-for-bit reproducibility unless all required backend controls are defined.

Recommended fields:

```json
{
  "temperature": 0.2,
  "top_p": 0.9,
  "max_tokens": 1024,
  "seed": 12345,
  "timeout_ms": 120000,
  "backend_profile": "requires definition",
  "prompt_template": "requires definition"
}
```

Validation:

- `temperature` must be number or null.
- `top_p` must be number or null.
- `max_tokens` must be integer or null.
- `seed` must be integer or null.
- `timeout_ms` must be positive integer.
- Unknown config fields are allowed only if namespaced or documented.

Fields requiring later definition:

- `backend_profile`
- `prompt_template`
- exact numeric ranges for `temperature`, `top_p`, and `max_tokens`

## Stage 1 Responses

Field:

```json
"stage1_responses": []
```

Required array.

Each item shape:

```json
{
  "model_id": "local/model-a",
  "status": "success",
  "response": "Raw response text.",
  "error_type": null,
  "error_message": null,
  "latency_ms": 1532,
  "tokens_used": {
    "prompt_tokens": 100,
    "completion_tokens": 220,
    "total_tokens": 320,
    "trusted": false
  },
  "timestamp": "2026-04-26T12:00:03Z"
}
```

Required fields:

- `model_id`
- `status`
- `response`
- `error_type`
- `error_message`
- `latency_ms`
- `timestamp`

Optional fields:

- `tokens_used`

Allowed `status` values:

- `success`
- `error`

Validation:

- `stage1_responses` must contain exactly one record per model in `models`.
- No model attempt may be silently dropped.
- `model_id` must be in top-level `models`.
- `status` must be `success` or `error`.
- If `status == "success"`:
  - `response` must be a non-empty string.
  - `error_type` must be null.
  - `error_message` must be null.
- If `status == "error"`:
  - `response` must be null.
  - `error_type` must be one value from the closed error taxonomy.
  - `error_message` must be a non-empty string.
- `latency_ms` must be a non-negative number.
- `timestamp` must be an ISO 8601 timestamp string.
- `tokens_used`, if present, must include `trusted`.
- `tokens_used.trusted` must be false unless llm_lab has an explicit trusted token counter. Backend-reported token usage must not be trusted by default.

## Stage 2 Reviews and Rankings

Top-level field:

```json
"label_to_model": {}
```

Required object.

Purpose:

- Stores the canonical mapping from anonymous response labels to model IDs.

Validation:

- Keys must use the format `Response A`, `Response B`, etc.
- Values must be model IDs from top-level `models`.
- Values must be unique.
- The mapping must include only Stage 1 models that produced `status == "success"`.
- The order implied by labels must be deterministic. Recommended rule: preserve the order of successful Stage 1 records as stored.

Field:

```json
"stage2_reviews": []
```

Required array.

Each item shape:

```json
{
  "reviewer_model_id": "local/model-a",
  "reviewed_labels": {
    "Response A": "local/model-a",
    "Response B": "local/model-b"
  },
  "status": "success",
  "raw_review_text": "Review text.",
  "parsed_ranking": [
    "Response B",
    "Response A"
  ],
  "error_type": null,
  "error_message": null,
  "latency_ms": 2410,
  "timestamp": "2026-04-26T12:00:07Z"
}
```

Required fields:

- `reviewer_model_id`
- `reviewed_labels`
- `status`
- `raw_review_text`
- `parsed_ranking`
- `error_type`
- `error_message`
- `latency_ms`
- `timestamp`

Allowed `status` values:

- `success`
- `error`

Validation:

- `reviewer_model_id` must be a model ID from top-level `models` or another explicitly configured reviewer model. If external reviewer models are allowed, this requires definition.
- `reviewed_labels` must exactly equal top-level `label_to_model` for the experiment.
- Each review must preserve both raw review text and parsed structure.
- If `status == "success"`:
  - `raw_review_text` must be a non-empty string.
  - `parsed_ranking` must be a non-empty array.
  - `parsed_ranking` must contain each key from `label_to_model` exactly once.
  - `error_type` must be null.
  - `error_message` must be null.
- If `status == "error"`:
  - `raw_review_text` may be a string or null.
  - `parsed_ranking` must be an empty array.
  - `error_type` must be one value from the closed error taxonomy.
  - `error_message` must be a non-empty string.
- Missing ranking output must be `status == "error"` with `error_type == "malformed_response"`.
- Malformed ranking output must be `status == "error"` with `error_type == "malformed_response"`.
- `latency_ms` must be a non-negative number.
- `timestamp` must be an ISO 8601 timestamp string.

## Aggregate Rankings

Field:

```json
"aggregate_rankings": []
```

Required array.

Each item shape:

```json
{
  "model_id": "local/model-b",
  "average_rank": 1.33,
  "rankings_count": 3,
  "valid": true
}
```

Required fields:

- `model_id`
- `average_rank`
- `rankings_count`
- `valid`

Validation:

- Aggregation must be reproducible from stored `stage2_reviews`.
- Only reviews with `status == "success"` may contribute to aggregation.
- `model_id` must be present in `label_to_model` values.
- `average_rank` must be a positive number when `valid == true`.
- `average_rank` must be null when `valid == false`.
- `rankings_count` must be an integer greater than or equal to zero.
- `valid` must be boolean.

Recommended deterministic aggregation rule:

1. Ignore Stage 2 records where `status == "error"`.
2. For each successful review, assign rank position starting at `1`.
3. Convert each label in `parsed_ranking` to `model_id` using `label_to_model`.
4. For each model, compute average of all observed rank positions.
5. Set `rankings_count` to the number of successful reviews that ranked the model.
6. Set `valid == true` if `rankings_count > 0`.
7. Set `valid == false` if `rankings_count == 0`.
8. Sort ascending by `average_rank`; ties sort lexicographically by `model_id`.

## Stage 3 Synthesis

Field:

```json
"stage3_synthesis": {}
```

Required object.

Shape:

```json
{
  "model_id": "local/model-chairman",
  "status": "success",
  "response": "Final synthesized answer.",
  "error_type": null,
  "error_message": null,
  "latency_ms": 3012,
  "timestamp": "2026-04-26T12:00:12Z"
}
```

Required fields:

- `model_id`
- `status`
- `response`
- `error_type`
- `error_message`
- `latency_ms`
- `timestamp`

Allowed `status` values:

- `success`
- `error`

Validation:

- `model_id` must be a non-empty string.
- If `status == "success"`:
  - `response` must be a non-empty string.
  - `error_type` must be null.
  - `error_message` must be null.
- If `status == "error"`:
  - `response` must be null.
  - `error_type` must be one value from the closed error taxonomy.
  - `error_message` must be a non-empty string.
- Empty synthesis response must be `status == "error"` with `error_type == "malformed_response"`.
- Invalid synthesis response must be `status == "error"` with `error_type == "malformed_response"`.
- `latency_ms` must be a non-negative number.
- `timestamp` must be an ISO 8601 timestamp string.

## Error Model

All stages must use the same closed error taxonomy.

Allowed `error_type` values:

- `invalid_request`
- `model_not_available`
- `timeout`
- `generation_failed`
- `malformed_response`
- `unsupported_feature`
- `unknown_error`

Definitions:

| Error type | Meaning |
|---|---|
| `invalid_request` | The lab request or stage input is structurally invalid. |
| `model_not_available` | The selected model cannot be found, loaded, or selected in the current lab environment. |
| `timeout` | The stage or model call exceeded its configured timeout. |
| `generation_failed` | The model call started but failed during generation. |
| `malformed_response` | A model or stage returned a response that cannot satisfy this contract. |
| `unsupported_feature` | The requested lab feature is not supported by the selected backend or stage. |
| `unknown_error` | The failure does not fit any defined category. This must be rare and should include a useful `error_message`. |

Validation:

- `error_type` must be null on success.
- `error_type` must be non-null on error.
- `error_message` must be null on success.
- `error_message` must be non-empty on error.
- Raw backend error payloads must not be stored as structured provider-specific schemas. Store normalized text in `error_message`.

## Metadata and Observability

Field:

```json
"metadata": {}
```

Required object.

Shape:

```json
{
  "total_latency_ms": 12000,
  "per_stage_latency": {
    "stage1_ms": 2000,
    "stage2_ms": 5000,
    "stage3_ms": 3012
  },
  "environment_snapshot": {
    "llm_lab_version": "requires definition",
    "host_id": "requires definition",
    "runtime_profile": "requires definition"
  }
}
```

Required fields:

- `total_latency_ms`
- `per_stage_latency`

Optional fields:

- `environment_snapshot`

Validation:

- `total_latency_ms` must be a non-negative number.
- `per_stage_latency.stage1_ms` must be a non-negative number.
- `per_stage_latency.stage2_ms` must be a non-negative number.
- `per_stage_latency.stage3_ms` must be a non-negative number.
- `environment_snapshot`, if present, must not include secrets.
- `environment_snapshot`, if present, must not include raw prompts or raw responses.

Fields requiring later definition:

- `llm_lab_version`
- `host_id`
- `runtime_profile`

### `notes`

Optional string.

Validation:

- Must be human-authored or lab-authored free text.
- Must not be used by validators.
- Must not change artifact semantics.

## Persistence Format

Canonical format:

- One JSON file per experiment.

Recommended path shape:

```text
runtime_lab/llm_lab/artifacts/{experiment_id}.json
```

Rules:

- File contents must be one complete JSON object.
- File must include `schema_version`.
- Artifact file must be treated as immutable after finalization.
- If updates are required during execution, write to a temporary or in-progress file and finalize with an atomic rename. Exact implementation requires definition.

Optional event log:

```text
runtime_lab/llm_lab/artifacts/{experiment_id}.events.jsonl
```

JSONL event log constraints:

- Optional.
- Used for streaming/progress reconstruction only.
- Not the canonical artifact.
- Each line must be a complete JSON object.
- Each event must include:
  - `schema_version`
  - `experiment_id`
  - `event_type`
  - `timestamp`
  - `payload`

Recommended event types:

- `experiment_started`
- `stage1_model_started`
- `stage1_model_completed`
- `stage2_review_started`
- `stage2_review_completed`
- `stage3_started`
- `stage3_completed`
- `experiment_completed`
- `experiment_failed`

Migration:

- Consumers must inspect `schema_version`.
- Unknown schema versions must not be silently accepted.
- Migration rules require definition when `v2` is introduced.

## Validation Rules

Artifact-level validation:

- Required top-level fields must exist.
- No required field may be null unless explicitly allowed.
- `experiment_id` must be a valid UUID.
- All timestamps must be valid ISO 8601 strings.
- `models` must be non-empty and unique.
- `stage1_responses` must include one record per model in `models`.
- No failed model attempt may be omitted.
- `label_to_model` must map only successful Stage 1 models.
- `stage2_reviews.reviewed_labels` must exactly match top-level `label_to_model`.
- Successful Stage 2 reviews must rank every label exactly once.
- Failed Stage 2 reviews must preserve raw text when available and mark parsed ranking as empty.
- `aggregate_rankings` must be reproducible from successful Stage 2 reviews.
- Successful Stage 3 synthesis must have a non-empty response.
- All stages must use the same error taxonomy.
- Backend-specific provider response shapes must not appear as required contract fields.

Success validation:

- A stage item with `status == "success"` must not contain `error_type` or `error_message`.
- A stage item with `status == "success"` must contain a valid non-empty response or parsed output, depending on stage.

Error validation:

- A stage item with `status == "error"` must contain `error_type`.
- A stage item with `status == "error"` must contain `error_message`.
- A stage item with `status == "error"` must not masquerade as usable output.

## Example Valid Artifact

```json
{
  "schema_version": "llm_lab.experiment.v1",
  "experiment_id": "11111111-1111-4111-8111-111111111111",
  "created_at": "2026-04-26T12:00:00Z",
  "input": {
    "user_input": "Compare local and remote LLM inference for a hardening phase."
  },
  "models": [
    "local/model-a",
    "local/model-b"
  ],
  "config": {
    "temperature": 0.2,
    "top_p": 0.9,
    "max_tokens": 512,
    "seed": 42,
    "timeout_ms": 120000,
    "backend_profile": "requires definition",
    "prompt_template": "requires definition"
  },
  "stage1_responses": [
    {
      "model_id": "local/model-a",
      "status": "success",
      "response": "Local inference improves data control but requires resource management.",
      "error_type": null,
      "error_message": null,
      "latency_ms": 1100,
      "tokens_used": {
        "prompt_tokens": 20,
        "completion_tokens": 30,
        "total_tokens": 50,
        "trusted": false
      },
      "timestamp": "2026-04-26T12:00:02Z"
    },
    {
      "model_id": "local/model-b",
      "status": "success",
      "response": "Remote inference simplifies operations but adds network and vendor dependency.",
      "error_type": null,
      "error_message": null,
      "latency_ms": 1300,
      "tokens_used": {
        "prompt_tokens": 20,
        "completion_tokens": 28,
        "total_tokens": 48,
        "trusted": false
      },
      "timestamp": "2026-04-26T12:00:02Z"
    }
  ],
  "label_to_model": {
    "Response A": "local/model-a",
    "Response B": "local/model-b"
  },
  "stage2_reviews": [
    {
      "reviewer_model_id": "local/model-a",
      "reviewed_labels": {
        "Response A": "local/model-a",
        "Response B": "local/model-b"
      },
      "status": "success",
      "raw_review_text": "Both responses are valid. FINAL RANKING:\n1. Response B\n2. Response A",
      "parsed_ranking": [
        "Response B",
        "Response A"
      ],
      "error_type": null,
      "error_message": null,
      "latency_ms": 900,
      "timestamp": "2026-04-26T12:00:04Z"
    },
    {
      "reviewer_model_id": "local/model-b",
      "reviewed_labels": {
        "Response A": "local/model-a",
        "Response B": "local/model-b"
      },
      "status": "success",
      "raw_review_text": "Response A is more precise. FINAL RANKING:\n1. Response A\n2. Response B",
      "parsed_ranking": [
        "Response A",
        "Response B"
      ],
      "error_type": null,
      "error_message": null,
      "latency_ms": 950,
      "timestamp": "2026-04-26T12:00:04Z"
    }
  ],
  "aggregate_rankings": [
    {
      "model_id": "local/model-a",
      "average_rank": 1.5,
      "rankings_count": 2,
      "valid": true
    },
    {
      "model_id": "local/model-b",
      "average_rank": 1.5,
      "rankings_count": 2,
      "valid": true
    }
  ],
  "stage3_synthesis": {
    "model_id": "local/model-chairman",
    "status": "success",
    "response": "Local inference favors control and offline operation; remote inference favors operational simplicity but adds external dependency.",
    "error_type": null,
    "error_message": null,
    "latency_ms": 1400,
    "timestamp": "2026-04-26T12:00:06Z"
  },
  "metadata": {
    "total_latency_ms": 6000,
    "per_stage_latency": {
      "stage1_ms": 1300,
      "stage2_ms": 950,
      "stage3_ms": 1400
    },
    "environment_snapshot": {
      "llm_lab_version": "requires definition",
      "host_id": "requires definition",
      "runtime_profile": "requires definition"
    }
  },
  "notes": "Valid artifact example."
}
```

## Example Artifact With Errors

```json
{
  "schema_version": "llm_lab.experiment.v1",
  "experiment_id": "22222222-2222-4222-8222-222222222222",
  "created_at": "2026-04-26T12:10:00Z",
  "input": {
    "user_input": "Summarize deterministic experiment logging."
  },
  "models": [
    "local/model-a",
    "local/model-b",
    "local/model-c"
  ],
  "config": {
    "temperature": 0.0,
    "top_p": 1.0,
    "max_tokens": 256,
    "seed": 7,
    "timeout_ms": 60000,
    "backend_profile": "requires definition",
    "prompt_template": "requires definition"
  },
  "stage1_responses": [
    {
      "model_id": "local/model-a",
      "status": "success",
      "response": "A deterministic log should preserve every attempted step.",
      "error_type": null,
      "error_message": null,
      "latency_ms": 800,
      "timestamp": "2026-04-26T12:10:01Z"
    },
    {
      "model_id": "local/model-b",
      "status": "error",
      "response": null,
      "error_type": "timeout",
      "error_message": "Model call exceeded timeout_ms.",
      "latency_ms": 60000,
      "timestamp": "2026-04-26T12:11:00Z"
    },
    {
      "model_id": "local/model-c",
      "status": "success",
      "response": "The artifact must store both successes and failures.",
      "error_type": null,
      "error_message": null,
      "latency_ms": 900,
      "timestamp": "2026-04-26T12:10:01Z"
    }
  ],
  "label_to_model": {
    "Response A": "local/model-a",
    "Response B": "local/model-c"
  },
  "stage2_reviews": [
    {
      "reviewer_model_id": "local/model-a",
      "reviewed_labels": {
        "Response A": "local/model-a",
        "Response B": "local/model-c"
      },
      "status": "success",
      "raw_review_text": "FINAL RANKING:\n1. Response A\n2. Response B",
      "parsed_ranking": [
        "Response A",
        "Response B"
      ],
      "error_type": null,
      "error_message": null,
      "latency_ms": 700,
      "timestamp": "2026-04-26T12:11:02Z"
    },
    {
      "reviewer_model_id": "local/model-c",
      "reviewed_labels": {
        "Response A": "local/model-a",
        "Response B": "local/model-c"
      },
      "status": "error",
      "raw_review_text": "Both are good, but no valid ranking was provided.",
      "parsed_ranking": [],
      "error_type": "malformed_response",
      "error_message": "Reviewer response did not contain a complete ranking over all labels.",
      "latency_ms": 750,
      "timestamp": "2026-04-26T12:11:02Z"
    }
  ],
  "aggregate_rankings": [
    {
      "model_id": "local/model-a",
      "average_rank": 1.0,
      "rankings_count": 1,
      "valid": true
    },
    {
      "model_id": "local/model-c",
      "average_rank": 2.0,
      "rankings_count": 1,
      "valid": true
    }
  ],
  "stage3_synthesis": {
    "model_id": "local/model-chairman",
    "status": "error",
    "response": null,
    "error_type": "generation_failed",
    "error_message": "Synthesis model failed before producing a valid response.",
    "latency_ms": 1200,
    "timestamp": "2026-04-26T12:11:04Z"
  },
  "metadata": {
    "total_latency_ms": 64000,
    "per_stage_latency": {
      "stage1_ms": 60000,
      "stage2_ms": 750,
      "stage3_ms": 1200
    },
    "environment_snapshot": {
      "llm_lab_version": "requires definition",
      "host_id": "requires definition",
      "runtime_profile": "requires definition"
    }
  },
  "notes": "Error artifact example. Failed model and malformed review are explicitly preserved."
}
```

## Required Invariants

- The artifact must be self-contained.
- The artifact must not require external provider schemas to interpret.
- The artifact must preserve every Stage 1 model attempt.
- The artifact must preserve failed reviews.
- The artifact must preserve raw review text when available.
- The artifact must preserve parsed rankings separately from raw text.
- The artifact must not treat empty response text as success.
- The artifact must not treat malformed ranking text as success.
- The artifact must not treat failed synthesis as a valid final answer.
- The artifact must include `schema_version`.
- The artifact must use the closed error taxonomy.
- The artifact must keep `llm_lab` experiment data separate from NUCLEO core runtime contracts.
