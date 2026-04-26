#!/usr/bin/env python3
"""Minimal deterministic experiment runner for runtime_lab/llm_lab."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

from experiment_artifact import (
    build_artifact,
    calculate_aggregate_rankings,
    error_record,
    make_label_to_model,
    new_experiment_id,
    parse_ranking,
    success_record,
    utc_now,
    write_artifact_atomic,
)
from experiment_validator import ArtifactValidationError, validate_artifact
from model_adapter import AdapterMode, call_model


LAB_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = LAB_DIR / "artifacts"
MOCK_SUCCESS_MODELS = ["mock/qwen", "mock/mistral", "mock/llama3.1:8b"]
MOCK_ERROR_STAGE1_MODELS = ["mock/qwen", "mock/mistral-unavailable", "mock/llama3.1:8b-empty"]
MOCK_ERROR_REVIEWERS = ["mock/qwen", "mock/llama3.1:8b-bad-ranking"]


def run_experiment(
    *,
    user_input: str,
    stage1_responders: list[str],
    stage2_reviewers: list[str],
    stage3_chairman: str,
    adapter_mode: AdapterMode,
    config: dict[str, Any],
    notes: str | None = None,
) -> Path:
    experiment_id = new_experiment_id()
    created_at = utc_now()
    total_start = time.perf_counter()

    stage1_start = time.perf_counter()
    stage1_responses = [
        _stage1_call(
            model_id,
            user_input,
            adapter_mode=adapter_mode,
            config=config,
            experiment_id=experiment_id,
        )
        for model_id in stage1_responders
    ]
    stage1_ms = elapsed_ms(stage1_start)

    label_to_model = make_label_to_model(stage1_responses)

    stage2_start = time.perf_counter()
    stage2_reviews = [
        _stage2_call(
            reviewer_model_id,
            user_input,
            stage1_responses,
            label_to_model,
            adapter_mode=adapter_mode,
            config=config,
            experiment_id=experiment_id,
        )
        for reviewer_model_id in stage2_reviewers
    ]
    stage2_ms = elapsed_ms(stage2_start)

    aggregate_rankings = calculate_aggregate_rankings(stage2_reviews, label_to_model)

    stage3_start = time.perf_counter()
    stage3_synthesis = _stage3_call(
        stage3_chairman,
        user_input,
        stage1_responses,
        stage2_reviews,
        aggregate_rankings,
        adapter_mode=adapter_mode,
        config=config,
        experiment_id=experiment_id,
    )
    stage3_ms = elapsed_ms(stage3_start)

    completed_at = utc_now()
    metadata = {
        "total_latency_ms": elapsed_ms(total_start),
        "per_stage_latency": {
            "stage1_ms": stage1_ms,
            "stage2_ms": stage2_ms,
            "stage3_ms": stage3_ms,
        },
        "environment_snapshot": {
            "llm_lab_version": "llm_lab.experiment_runner.v1",
            "host_id": "requires definition",
            "runtime_profile": adapter_mode,
        },
    }

    artifact = build_artifact(
        experiment_id=experiment_id,
        created_at=created_at,
        completed_at=completed_at,
        user_input=user_input,
        models={
            "stage1_responders": stage1_responders,
            "stage2_reviewers": stage2_reviewers,
            "stage3_chairman": stage3_chairman,
        },
        config=config,
        stage1_responses=stage1_responses,
        label_to_model=label_to_model,
        stage2_reviews=stage2_reviews,
        aggregate_rankings=aggregate_rankings,
        stage3_synthesis=stage3_synthesis,
        metadata=metadata,
        notes=notes,
    )
    validate_artifact(artifact)
    return write_artifact_atomic(artifact, ARTIFACTS_DIR)


def _stage1_call(
    model_id: str,
    user_input: str,
    *,
    adapter_mode: AdapterMode,
    config: dict[str, Any],
    experiment_id: str,
) -> dict[str, Any]:
    result = call_model(
        model_id,
        user_input,
        mode=adapter_mode,
        timeout_ms=int(config["timeout_ms"]),
    )
    log_stage_result(experiment_id, "stage1", model_id, result.status, result.latency_ms, result.error_type)
    if result.status == "success":
        return success_record(
            model_key=model_id,
            model_field="model_id",
            response_field="response",
            response=result.output or "",
            latency_ms=result.latency_ms,
            extra={"tokens_used": {"trusted": False}},
        )
    return error_record(
        model_key=model_id,
        model_field="model_id",
        response_field="response",
        error_type=result.error_type or "unknown_error",
        error_message=result.error_message or "Unknown Stage 1 error.",
        latency_ms=result.latency_ms,
    )


def _stage2_call(
    reviewer_model_id: str,
    user_input: str,
    stage1_responses: list[dict[str, Any]],
    label_to_model: dict[str, str],
    *,
    adapter_mode: AdapterMode,
    config: dict[str, Any],
    experiment_id: str,
) -> dict[str, Any]:
    if not label_to_model:
        return error_record(
            model_key=reviewer_model_id,
            model_field="reviewer_model_id",
            response_field="raw_review_text",
            error_type="invalid_request",
            error_message="Stage 2 cannot run because Stage 1 produced no successful responses.",
            latency_ms=0,
            extra={"reviewed_labels": {}, "parsed_ranking": []},
        )

    prompt = build_review_prompt(user_input, stage1_responses, label_to_model)
    result = call_model(
        reviewer_model_id,
        prompt,
        mode=adapter_mode,
        timeout_ms=int(config["timeout_ms"]),
    )
    if result.status != "success":
        log_stage_result(experiment_id, "stage2", reviewer_model_id, result.status, result.latency_ms, result.error_type)
        return error_record(
            model_key=reviewer_model_id,
            model_field="reviewer_model_id",
            response_field="raw_review_text",
            error_type=result.error_type or "unknown_error",
            error_message=result.error_message or "Unknown Stage 2 error.",
            latency_ms=result.latency_ms,
            extra={"reviewed_labels": dict(label_to_model), "parsed_ranking": []},
        )

    raw_text = result.output or ""
    parsed, parse_error = parse_ranking(raw_text, list(label_to_model.keys()))
    if parse_error:
        log_stage_result(
            experiment_id,
            "stage2",
            reviewer_model_id,
            "error",
            result.latency_ms,
            "malformed_response",
        )
        return {
            "reviewer_model_id": reviewer_model_id,
            "reviewed_labels": dict(label_to_model),
            "status": "error",
            "raw_review_text": raw_text,
            "parsed_ranking": [],
            "error_type": "malformed_response",
            "error_message": parse_error,
            "latency_ms": result.latency_ms,
            "timestamp": utc_now(),
        }

    log_stage_result(experiment_id, "stage2", reviewer_model_id, "success", result.latency_ms, None)
    return {
        "reviewer_model_id": reviewer_model_id,
        "reviewed_labels": dict(label_to_model),
        "status": "success",
        "raw_review_text": raw_text,
        "parsed_ranking": parsed,
        "error_type": None,
        "error_message": None,
        "latency_ms": result.latency_ms,
        "timestamp": utc_now(),
    }


def _stage3_call(
    chairman_model_id: str,
    user_input: str,
    stage1_responses: list[dict[str, Any]],
    stage2_reviews: list[dict[str, Any]],
    aggregate_rankings: list[dict[str, Any]],
    *,
    adapter_mode: AdapterMode,
    config: dict[str, Any],
    experiment_id: str,
) -> dict[str, Any]:
    if not any(record.get("status") == "success" for record in stage1_responses):
        return error_record(
            model_key=chairman_model_id,
            model_field="model_id",
            response_field="response",
            error_type="invalid_request",
            error_message="Stage 3 cannot run because Stage 1 produced no successful responses.",
            latency_ms=0,
        )

    prompt = build_synthesis_prompt(user_input, stage1_responses, stage2_reviews, aggregate_rankings)
    result = call_model(
        chairman_model_id,
        prompt,
        mode=adapter_mode,
        timeout_ms=int(config["timeout_ms"]),
    )
    log_stage_result(experiment_id, "stage3", chairman_model_id, result.status, result.latency_ms, result.error_type)
    if result.status == "success":
        return success_record(
            model_key=chairman_model_id,
            model_field="model_id",
            response_field="response",
            response=result.output or "",
            latency_ms=result.latency_ms,
        )
    return error_record(
        model_key=chairman_model_id,
        model_field="model_id",
        response_field="response",
        error_type=result.error_type or "unknown_error",
        error_message=result.error_message or "Unknown Stage 3 error.",
        latency_ms=result.latency_ms,
    )


def build_review_prompt(
    user_input: str,
    stage1_responses: list[dict[str, Any]],
    label_to_model: dict[str, str],
) -> str:
    by_model = {record["model_id"]: record["response"] for record in stage1_responses if record["status"] == "success"}
    response_blocks = []
    for label, model_id in label_to_model.items():
        response_blocks.append(f"{label}:\n{by_model[model_id]}")

    return (
        "Review the anonymized responses to the user input.\n\n"
        f"User input:\n{user_input}\n\n"
        + "\n\n".join(response_blocks)
        + "\n\nFINAL RANKING is required. Rank every label exactly once.\n"
        "FINAL RANKING:\n"
    )


def build_synthesis_prompt(
    user_input: str,
    stage1_responses: list[dict[str, Any]],
    stage2_reviews: list[dict[str, Any]],
    aggregate_rankings: list[dict[str, Any]],
) -> str:
    return (
        "SYNTHESIZE_FINAL\n"
        "Produce one final answer from stored experiment artifacts.\n\n"
        f"User input:\n{user_input}\n\n"
        f"Stage 1:\n{stage1_responses}\n\n"
        f"Stage 2:\n{stage2_reviews}\n\n"
        f"Aggregate rankings:\n{aggregate_rankings}\n"
    )


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def log_stage_result(
    experiment_id: str,
    stage: str,
    model_id: str,
    status: str,
    latency_ms: float,
    error_type: str | None,
) -> None:
    print(
        " ".join(
            [
                "llm_lab_event",
                f"experiment_id={experiment_id}",
                f"stage={stage}",
                f"model_id={model_id}",
                f"status={status}",
                f"latency_ms={latency_ms}",
                f"error_type={error_type}",
            ]
        )
    )


def default_config(adapter_mode: AdapterMode, timeout_ms: int) -> dict[str, Any]:
    return {
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 1024,
        "seed": None,
        "timeout_ms": timeout_ms,
        "backend_profile": adapter_mode,
        "prompt_template": "llm_lab.council.v1",
    }


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def run_mock_pair(user_input: str, timeout_ms: int) -> list[Path]:
    success_config = default_config("mock_success", timeout_ms)
    errors_config = default_config("mock_errors", timeout_ms)
    return [
        run_experiment(
            user_input=user_input,
            stage1_responders=MOCK_SUCCESS_MODELS,
            stage2_reviewers=MOCK_SUCCESS_MODELS,
            stage3_chairman="mock/chairman",
            adapter_mode="mock_success",
            config=success_config,
            notes="Mock success artifact.",
        ),
        run_experiment(
            user_input=user_input,
            stage1_responders=MOCK_ERROR_STAGE1_MODELS,
            stage2_reviewers=MOCK_ERROR_REVIEWERS,
            stage3_chairman="mock/chairman-empty",
            adapter_mode="mock_errors",
            config=errors_config,
            notes="Mock error artifact.",
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a deterministic llm_lab experiment.")
    parser.add_argument("--input", required=True, help="User input for the experiment.")
    parser.add_argument(
        "--mode",
        choices=["mock", "mock-success", "mock-errors", "ollama"],
        default="mock",
        help="Execution mode. 'mock' writes one success artifact and one error artifact.",
    )
    parser.add_argument(
        "--stage1-models",
        default="qwen,mistral,llama3.1:8b",
        help="Comma-separated Stage 1 model IDs for ollama mode.",
    )
    parser.add_argument(
        "--stage2-reviewers",
        default="qwen,mistral,llama3.1:8b",
        help="Comma-separated Stage 2 reviewer model IDs for ollama mode.",
    )
    parser.add_argument(
        "--chairman",
        default="qwen",
        help="Stage 3 chairman model ID for ollama mode.",
    )
    parser.add_argument("--timeout-ms", type=int, default=120000)
    args = parser.parse_args()

    if args.mode == "mock":
        paths = safe_run(lambda: run_mock_pair(args.input, args.timeout_ms))
    elif args.mode == "mock-success":
        config = default_config("mock_success", args.timeout_ms)
        paths = safe_run(
            lambda: [
                run_experiment(
                    user_input=args.input,
                    stage1_responders=MOCK_SUCCESS_MODELS,
                    stage2_reviewers=MOCK_SUCCESS_MODELS,
                    stage3_chairman="mock/chairman",
                    adapter_mode="mock_success",
                    config=config,
                    notes="Mock success artifact.",
                )
            ]
        )
    elif args.mode == "mock-errors":
        config = default_config("mock_errors", args.timeout_ms)
        paths = safe_run(
            lambda: [
                run_experiment(
                    user_input=args.input,
                    stage1_responders=MOCK_ERROR_STAGE1_MODELS,
                    stage2_reviewers=MOCK_ERROR_REVIEWERS,
                    stage3_chairman="mock/chairman-empty",
                    adapter_mode="mock_errors",
                    config=config,
                    notes="Mock error artifact.",
                )
            ]
        )
    else:
        config = default_config("ollama", args.timeout_ms)
        paths = safe_run(
            lambda: [
                run_experiment(
                    user_input=args.input,
                    stage1_responders=parse_csv(args.stage1_models),
                    stage2_reviewers=parse_csv(args.stage2_reviewers),
                    stage3_chairman=args.chairman,
                    adapter_mode="ollama",
                    config=config,
                    notes="Real local Ollama llm_lab artifact.",
                )
            ]
        )

    for path in paths:
        print(f"Artifact written: {path}")


def safe_run(callback) -> list[Path]:
    try:
        return callback()
    except ArtifactValidationError as exc:
        print(f"VALIDATION_ERROR: artifact was not written: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
