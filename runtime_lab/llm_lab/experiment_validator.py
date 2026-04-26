"""Contract validator for llm_lab experiment artifacts."""

from __future__ import annotations

from datetime import datetime
import uuid
from typing import Any

from experiment_artifact import (
    SCHEMA_VERSION,
    VALID_ERROR_TYPES,
    VALID_EXPERIMENT_STATUSES,
    VALID_STATUSES,
    calculate_aggregate_rankings,
)


class ArtifactValidationError(ValueError):
    """Raised when an experiment artifact violates the lab contract."""


def validate_artifact(artifact: dict[str, Any]) -> None:
    """Validate an artifact without mutating or correcting it."""
    _validate_top_level(artifact)
    _validate_input(artifact)
    _validate_models(artifact)
    _validate_config(artifact)
    _validate_stage1(artifact)
    _validate_label_to_model(artifact)
    _validate_stage2(artifact)
    _validate_aggregate_rankings(artifact)
    _validate_stage3(artifact)
    _validate_metadata(artifact)
    _validate_global_status(artifact)


def _validate_top_level(artifact: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "experiment_id",
        "created_at",
        "completed_at",
        "status",
        "input",
        "models",
        "config",
        "stage1_responses",
        "label_to_model",
        "stage2_reviews",
        "aggregate_rankings",
        "stage3_synthesis",
        "metadata",
    }
    missing = sorted(required - artifact.keys())
    if missing:
        raise ArtifactValidationError(f"Missing required fields: {', '.join(missing)}")

    if artifact["schema_version"] != SCHEMA_VERSION:
        raise ArtifactValidationError("Unsupported schema_version.")
    try:
        uuid.UUID(artifact["experiment_id"])
    except (TypeError, ValueError) as exc:
        raise ArtifactValidationError("experiment_id must be a valid UUID.") from exc
    _require_timestamp(artifact["created_at"], "created_at")
    _require_timestamp(artifact["completed_at"], "completed_at")
    if artifact["status"] not in VALID_EXPERIMENT_STATUSES:
        raise ArtifactValidationError("Invalid experiment status.")


def _validate_input(artifact: dict[str, Any]) -> None:
    input_obj = artifact["input"]
    if not isinstance(input_obj, dict):
        raise ArtifactValidationError("input must be an object.")
    user_input = input_obj.get("user_input")
    if not isinstance(user_input, str) or not user_input.strip():
        raise ArtifactValidationError("input.user_input must be a non-empty string.")


def _validate_models(artifact: dict[str, Any]) -> None:
    models = artifact["models"]
    if not isinstance(models, dict):
        raise ArtifactValidationError("models must be a role object.")

    responders = models.get("stage1_responders")
    reviewers = models.get("stage2_reviewers")
    chairman = models.get("stage3_chairman")
    _require_unique_string_list(responders, "models.stage1_responders")
    _require_unique_string_list(reviewers, "models.stage2_reviewers")
    if not isinstance(chairman, str) or not chairman.strip():
        raise ArtifactValidationError("models.stage3_chairman must be a non-empty string.")


def _validate_config(artifact: dict[str, Any]) -> None:
    config = artifact["config"]
    if not isinstance(config, dict):
        raise ArtifactValidationError("config must be an object.")
    timeout_ms = config.get("timeout_ms")
    if not isinstance(timeout_ms, int) or timeout_ms <= 0:
        raise ArtifactValidationError("config.timeout_ms must be a positive integer.")
    for key in ("temperature", "top_p"):
        value = config.get(key)
        if value is not None and not isinstance(value, (int, float)):
            raise ArtifactValidationError(f"config.{key} must be number or null.")
    max_tokens = config.get("max_tokens")
    if max_tokens is not None and not isinstance(max_tokens, int):
        raise ArtifactValidationError("config.max_tokens must be integer or null.")
    seed = config.get("seed")
    if seed is not None and not isinstance(seed, int):
        raise ArtifactValidationError("config.seed must be integer or null.")


def _validate_stage1(artifact: dict[str, Any]) -> None:
    responders = artifact["models"]["stage1_responders"]
    records = artifact["stage1_responses"]
    if not isinstance(records, list):
        raise ArtifactValidationError("stage1_responses must be an array.")
    if len(records) != len(responders):
        raise ArtifactValidationError("stage1_responses must contain one record per responder.")

    ids = [record.get("model_id") for record in records if isinstance(record, dict)]
    if sorted(ids) != sorted(responders):
        raise ArtifactValidationError("stage1_responses model IDs do not match responders.")
    if len(ids) != len(set(ids)):
        raise ArtifactValidationError("stage1_responses contains duplicate model records.")

    for record in records:
        _validate_stage_record(record, response_field="response", model_field="model_id")
        if record["status"] == "success":
            tokens_used = record.get("tokens_used")
            if tokens_used is not None:
                if not isinstance(tokens_used, dict):
                    raise ArtifactValidationError("tokens_used must be an object when present.")
                if tokens_used.get("trusted") is not False:
                    raise ArtifactValidationError("tokens_used.trusted must be false unless explicitly trusted.")


def _validate_label_to_model(artifact: dict[str, Any]) -> None:
    mapping = artifact["label_to_model"]
    if not isinstance(mapping, dict):
        raise ArtifactValidationError("label_to_model must be an object.")

    successful_stage1 = [
        record["model_id"]
        for record in artifact["stage1_responses"]
        if record["status"] == "success"
    ]
    if sorted(mapping.values()) != sorted(successful_stage1):
        raise ArtifactValidationError("label_to_model must contain exactly successful Stage 1 models.")
    if len(mapping.values()) != len(set(mapping.values())):
        raise ArtifactValidationError("label_to_model contains duplicate model IDs.")

    expected_labels = [f"Response {chr(65 + index)}" for index in range(len(successful_stage1))]
    if list(mapping.keys()) != expected_labels:
        raise ArtifactValidationError("label_to_model labels must be deterministic Response A/B/C order.")


def _validate_stage2(artifact: dict[str, Any]) -> None:
    reviewers = artifact["models"]["stage2_reviewers"]
    records = artifact["stage2_reviews"]
    if not isinstance(records, list):
        raise ArtifactValidationError("stage2_reviews must be an array.")
    if len(records) != len(reviewers):
        raise ArtifactValidationError("stage2_reviews must contain one record per reviewer.")

    ids = [record.get("reviewer_model_id") for record in records if isinstance(record, dict)]
    if sorted(ids) != sorted(reviewers):
        raise ArtifactValidationError("stage2_reviews reviewer IDs do not match configured reviewers.")
    if len(ids) != len(set(ids)):
        raise ArtifactValidationError("stage2_reviews contains duplicate reviewer records.")

    for record in records:
        _validate_stage_record(
            record,
            response_field="raw_review_text",
            model_field="reviewer_model_id",
            allow_error_output=True,
        )
        if record.get("reviewed_labels") != artifact["label_to_model"]:
            raise ArtifactValidationError("stage2 review labels must match label_to_model.")
        parsed = record.get("parsed_ranking")
        if record["status"] == "success":
            if not isinstance(parsed, list):
                raise ArtifactValidationError("parsed_ranking must be an array.")
            labels = list(artifact["label_to_model"].keys())
            if sorted(parsed) != sorted(labels) or len(parsed) != len(set(parsed)):
                raise ArtifactValidationError("successful stage2 review has invalid parsed_ranking.")
        else:
            if parsed != []:
                raise ArtifactValidationError("failed stage2 review must have empty parsed_ranking.")
            if record.get("error_type") == "malformed_response":
                raw_text = record.get("raw_review_text")
                if raw_text is not None and not isinstance(raw_text, str):
                    raise ArtifactValidationError("failed malformed review raw text must be string or null.")


def _validate_aggregate_rankings(artifact: dict[str, Any]) -> None:
    aggregate = artifact["aggregate_rankings"]
    if not isinstance(aggregate, list):
        raise ArtifactValidationError("aggregate_rankings must be an array.")
    expected = calculate_aggregate_rankings(
        artifact["stage2_reviews"],
        artifact["label_to_model"],
    )
    if aggregate != expected:
        raise ArtifactValidationError("aggregate_rankings is not reproducible from stage2_reviews.")
    for item in aggregate:
        if not isinstance(item.get("model_id"), str) or not item["model_id"].strip():
            raise ArtifactValidationError("aggregate model_id must be non-empty string.")
        if not isinstance(item.get("rankings_count"), int) or item["rankings_count"] < 0:
            raise ArtifactValidationError("aggregate rankings_count must be non-negative integer.")
        if not isinstance(item.get("valid"), bool):
            raise ArtifactValidationError("aggregate valid must be boolean.")
        if item["valid"]:
            if not isinstance(item.get("average_rank"), (int, float)) or item["average_rank"] <= 0:
                raise ArtifactValidationError("valid aggregate average_rank must be positive number.")
        elif item.get("average_rank") is not None:
            raise ArtifactValidationError("invalid aggregate average_rank must be null.")


def _validate_stage3(artifact: dict[str, Any]) -> None:
    synthesis = artifact["stage3_synthesis"]
    _validate_stage_record(synthesis, response_field="response", model_field="model_id")
    if synthesis.get("model_id") != artifact["models"]["stage3_chairman"]:
        raise ArtifactValidationError("stage3_synthesis model_id must match configured chairman.")


def _validate_metadata(artifact: dict[str, Any]) -> None:
    metadata = artifact["metadata"]
    if not isinstance(metadata, dict):
        raise ArtifactValidationError("metadata must be an object.")
    total = metadata.get("total_latency_ms")
    if not isinstance(total, (int, float)) or total < 0:
        raise ArtifactValidationError("metadata.total_latency_ms must be non-negative number.")
    per_stage = metadata.get("per_stage_latency")
    if not isinstance(per_stage, dict):
        raise ArtifactValidationError("metadata.per_stage_latency must be an object.")
    for key in ("stage1_ms", "stage2_ms", "stage3_ms"):
        value = per_stage.get(key)
        if not isinstance(value, (int, float)) or value < 0:
            raise ArtifactValidationError(f"metadata.per_stage_latency.{key} must be non-negative number.")
    env = metadata.get("environment_snapshot")
    if env is not None and not isinstance(env, dict):
        raise ArtifactValidationError("metadata.environment_snapshot must be an object when present.")


def _validate_global_status(artifact: dict[str, Any]) -> None:
    stage1_errors = any(record["status"] == "error" for record in artifact["stage1_responses"])
    stage2_errors = any(record["status"] == "error" for record in artifact["stage2_reviews"])
    stage3_success = artifact["stage3_synthesis"]["status"] == "success"

    if not stage3_success:
        expected = "error"
    elif stage1_errors or stage2_errors:
        expected = "partial_success"
    else:
        expected = "success"

    if artifact["status"] != expected:
        raise ArtifactValidationError(f"Invalid experiment status: expected {expected}.")


def _validate_stage_record(
    record: dict[str, Any],
    *,
    response_field: str,
    model_field: str,
    allow_error_output: bool = False,
) -> None:
    if not isinstance(record, dict):
        raise ArtifactValidationError("stage record must be an object.")
    if not isinstance(record.get(model_field), str) or not record[model_field].strip():
        raise ArtifactValidationError(f"{model_field} must be a non-empty string.")
    status = record.get("status")
    if status not in VALID_STATUSES:
        raise ArtifactValidationError("Invalid stage record status.")
    latency = record.get("latency_ms")
    if not isinstance(latency, (int, float)) or latency < 0:
        raise ArtifactValidationError("latency_ms must be non-negative number.")
    _require_timestamp(record.get("timestamp"), "stage timestamp")

    if status == "success":
        value = record.get(response_field)
        if not isinstance(value, str) or not value.strip():
            raise ArtifactValidationError("successful stage record has empty output.")
        if record.get("error_type") is not None or record.get("error_message") is not None:
            raise ArtifactValidationError("successful stage record must not contain error fields.")
    else:
        if record.get("error_type") not in VALID_ERROR_TYPES:
            raise ArtifactValidationError("invalid error_type.")
        if not isinstance(record.get("error_message"), str) or not record["error_message"].strip():
            raise ArtifactValidationError("error_message must be non-empty for failed records.")
        if not allow_error_output and record.get(response_field) is not None:
            raise ArtifactValidationError("failed stage record must not contain usable output.")


def _require_unique_string_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not value:
        raise ArtifactValidationError(f"{field_name} must be a non-empty array.")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ArtifactValidationError(f"{field_name} must contain non-empty strings.")
    if len(value) != len(set(value)):
        raise ArtifactValidationError(f"{field_name} contains duplicates.")


def _require_timestamp(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ArtifactValidationError(f"{field_name} must be a timestamp string.")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ArtifactValidationError(f"{field_name} must be ISO 8601.") from exc
    if parsed.tzinfo is None:
        raise ArtifactValidationError(f"{field_name} must include timezone.")
