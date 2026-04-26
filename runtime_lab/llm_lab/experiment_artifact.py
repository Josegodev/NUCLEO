"""Deterministic artifact helpers for llm_lab experiments.

This module is intentionally scoped to runtime_lab/llm_lab. It does not import
or call NUCLEO runtime components.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "llm_lab.experiment.v1"
VALID_STATUSES = {"success", "error"}
VALID_EXPERIMENT_STATUSES = {"success", "partial_success", "error"}
VALID_ERROR_TYPES = {
    "invalid_request",
    "model_not_available",
    "timeout",
    "generation_failed",
    "malformed_response",
    "unsupported_feature",
    "unknown_error",
}


class ArtifactValidationError(ValueError):
    """Raised when an experiment artifact violates the lab contract."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_experiment_id() -> str:
    return str(uuid.uuid4())


def success_record(
    *,
    model_key: str,
    model_field: str,
    response_field: str,
    response: str,
    latency_ms: float,
    timestamp: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not response.strip():
        return error_record(
            model_key=model_key,
            model_field=model_field,
            response_field=response_field,
            error_type="malformed_response",
            error_message="Model returned empty output.",
            latency_ms=latency_ms,
            timestamp=timestamp,
            extra=extra,
        )

    record = {
        model_field: model_key,
        "status": "success",
        response_field: response,
        "error_type": None,
        "error_message": None,
        "latency_ms": latency_ms,
        "timestamp": timestamp or utc_now(),
    }
    if extra:
        record.update(extra)
    return record


def error_record(
    *,
    model_key: str,
    model_field: str,
    response_field: str,
    error_type: str,
    error_message: str,
    latency_ms: float,
    timestamp: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if error_type not in VALID_ERROR_TYPES:
        error_type = "unknown_error"
    record = {
        model_field: model_key,
        "status": "error",
        response_field: None,
        "error_type": error_type,
        "error_message": error_message or "Unknown error.",
        "latency_ms": latency_ms,
        "timestamp": timestamp or utc_now(),
    }
    if extra:
        record.update(extra)
    return record


def make_label_to_model(stage1_responses: list[dict[str, Any]]) -> dict[str, str]:
    label_to_model: dict[str, str] = {}
    label_index = 0
    for record in stage1_responses:
        if record.get("status") != "success":
            continue
        label = f"Response {chr(65 + label_index)}"
        label_to_model[label] = record["model_id"]
        label_index += 1
    return label_to_model


def parse_ranking(raw_text: str, labels: list[str]) -> tuple[list[str], str | None]:
    """Parse and validate a ranking over the provided labels."""
    if not raw_text.strip():
        return [], "Review output was empty."

    search_area = raw_text.split("FINAL RANKING:", 1)[1] if "FINAL RANKING:" in raw_text else raw_text
    found = re.findall(r"Response [A-Z]", search_area)
    if not found:
        return [], "Review output did not contain response labels."

    known = set(labels)
    unknown = [label for label in found if label not in known]
    if unknown:
        return [], f"Review output referenced unknown labels: {', '.join(sorted(set(unknown)))}."

    if len(found) != len(set(found)):
        return [], "Review output ranked at least one label more than once."

    missing = [label for label in labels if label not in found]
    if missing:
        return [], f"Review output missed labels: {', '.join(missing)}."

    if len(found) != len(labels):
        return [], "Review output did not rank every label exactly once."

    return found, None


def calculate_aggregate_rankings(
    stage2_reviews: list[dict[str, Any]],
    label_to_model: dict[str, str],
) -> list[dict[str, Any]]:
    positions: dict[str, list[int]] = {model_id: [] for model_id in label_to_model.values()}

    for review in stage2_reviews:
        if review.get("status") != "success":
            continue
        for position, label in enumerate(review.get("parsed_ranking", []), start=1):
            model_id = label_to_model.get(label)
            if model_id is not None:
                positions.setdefault(model_id, []).append(position)

    aggregate: list[dict[str, Any]] = []
    for model_id in sorted(positions):
        ranks = positions[model_id]
        if ranks:
            aggregate.append(
                {
                    "model_id": model_id,
                    "average_rank": round(sum(ranks) / len(ranks), 2),
                    "rankings_count": len(ranks),
                    "valid": True,
                }
            )
        else:
            aggregate.append(
                {
                    "model_id": model_id,
                    "average_rank": None,
                    "rankings_count": 0,
                    "valid": False,
                }
            )

    aggregate.sort(
        key=lambda item: (
            not item["valid"],
            item["average_rank"] if item["average_rank"] is not None else float("inf"),
            item["model_id"],
        )
    )
    return aggregate


def determine_experiment_status(artifact: dict[str, Any]) -> str:
    stage1 = artifact["stage1_responses"]
    stage2 = artifact["stage2_reviews"]
    stage3 = artifact["stage3_synthesis"]

    if stage3.get("status") != "success":
        return "error"
    if any(record.get("status") == "error" for record in stage1):
        return "partial_success"
    if any(record.get("status") == "error" for record in stage2):
        return "partial_success"
    return "success"


def build_artifact(
    *,
    experiment_id: str,
    created_at: str,
    completed_at: str,
    user_input: str,
    models: dict[str, Any],
    config: dict[str, Any],
    stage1_responses: list[dict[str, Any]],
    label_to_model: dict[str, str],
    stage2_reviews: list[dict[str, Any]],
    aggregate_rankings: list[dict[str, Any]],
    stage3_synthesis: dict[str, Any],
    metadata: dict[str, Any],
    notes: str | None = None,
) -> dict[str, Any]:
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": experiment_id,
        "created_at": created_at,
        "completed_at": completed_at,
        "status": "error",
        "input": {"user_input": user_input},
        "models": models,
        "config": config,
        "stage1_responses": stage1_responses,
        "label_to_model": label_to_model,
        "stage2_reviews": stage2_reviews,
        "aggregate_rankings": aggregate_rankings,
        "stage3_synthesis": stage3_synthesis,
        "metadata": metadata,
    }
    artifact["status"] = determine_experiment_status(artifact)
    if notes:
        artifact["notes"] = notes
    return artifact


def validate_artifact(artifact: dict[str, Any]) -> None:
    from experiment_validator import validate_artifact as strict_validate_artifact

    strict_validate_artifact(artifact)
    return

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
    uuid.UUID(artifact["experiment_id"])
    if artifact["status"] not in VALID_EXPERIMENT_STATUSES:
        raise ArtifactValidationError("Invalid experiment status.")
    if not artifact["input"].get("user_input", "").strip():
        raise ArtifactValidationError("input.user_input must be non-empty.")

    responders = artifact["models"].get("stage1_responders", [])
    if not responders:
        raise ArtifactValidationError("models.stage1_responders must be non-empty.")
    if len(responders) != len(set(responders)):
        raise ArtifactValidationError("models.stage1_responders contains duplicates.")
    if len(artifact["stage1_responses"]) != len(responders):
        raise ArtifactValidationError("stage1_responses must contain one record per responder.")

    stage1_ids = [record.get("model_id") for record in artifact["stage1_responses"]]
    if sorted(stage1_ids) != sorted(responders):
        raise ArtifactValidationError("stage1_responses model IDs do not match responders.")

    for record in artifact["stage1_responses"]:
        _validate_stage_record(record, response_field="response")

    successful_stage1 = [record["model_id"] for record in artifact["stage1_responses"] if record["status"] == "success"]
    if sorted(artifact["label_to_model"].values()) != sorted(successful_stage1):
        raise ArtifactValidationError("label_to_model must contain exactly successful Stage 1 models.")

    for review in artifact["stage2_reviews"]:
        _validate_stage_record(review, response_field="raw_review_text")
        if review.get("reviewed_labels") != artifact["label_to_model"]:
            raise ArtifactValidationError("stage2 review labels must match label_to_model.")
        if review["status"] == "success":
            ranking = review.get("parsed_ranking", [])
            if sorted(ranking) != sorted(artifact["label_to_model"].keys()) or len(ranking) != len(set(ranking)):
                raise ArtifactValidationError("successful stage2 review has invalid parsed_ranking.")
        else:
            if review.get("parsed_ranking") != []:
                raise ArtifactValidationError("failed stage2 review must have empty parsed_ranking.")

    expected_aggregate = calculate_aggregate_rankings(
        artifact["stage2_reviews"],
        artifact["label_to_model"],
    )
    if artifact["aggregate_rankings"] != expected_aggregate:
        raise ArtifactValidationError("aggregate_rankings is not reproducible from stage2_reviews.")

    _validate_stage_record(artifact["stage3_synthesis"], response_field="response")


def _validate_stage_record(record: dict[str, Any], *, response_field: str) -> None:
    status = record.get("status")
    if status not in VALID_STATUSES:
        raise ArtifactValidationError("Invalid stage record status.")
    if record.get("latency_ms") is None or record["latency_ms"] < 0:
        raise ArtifactValidationError("latency_ms must be non-negative.")
    if not record.get("timestamp"):
        raise ArtifactValidationError("timestamp is required.")

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


def write_artifact_atomic(artifact: dict[str, Any], output_dir: Path) -> Path:
    validate_artifact(artifact)
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / f"{artifact['experiment_id']}.json"
    tmp_path = output_dir / f"{artifact['experiment_id']}.tmp.json"
    try:
        tmp_path.write_text(
            json.dumps(artifact, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        validate_artifact(json.loads(tmp_path.read_text(encoding="utf-8")))
        os.replace(tmp_path, final_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise
    return final_path
