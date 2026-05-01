from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.adapters.model_router import DEFAULT_TIMEOUT_MS, ModelRouter
from app.runtime.planner_augmentation import (
    LLMAssistedPlannerStrategy,
    LLMPlanOutputValidator,
    ModelRouterProposalProvider,
    _strip_json_fence,
)
from app.schemas.requests import AgentBackend, AgentRequest, AgentRunOptions
from app.tools.registry import ToolRegistry
from app.tools.registry import registry as production_registry


EVAL_VERSION = "agent_proposal_eval_result.v1"
DEFAULT_CASES_PATH = Path(__file__).with_name("agent_proposal_eval_cases.json")
DEFAULT_OUTPUT_DIR = Path(__file__).with_name("results")
DEFAULT_MODELS = ("llama3.1:8b", "gpt-4o-mini")
DEFAULT_BACKENDS = ("local", "openai")
RUNTIME_CANDIDATE_MIN_VALID_CONTRACT_RATE = 0.95
RUNTIME_CANDIDATE_MAX_FALLBACK_RATE = 0.10


def load_eval_cases(path: Path = DEFAULT_CASES_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != "agent_proposal_eval.v1":
        raise ValueError("unsupported eval cases version")

    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("eval cases must contain a non-empty cases list")

    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each eval case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError("each eval case requires a non-empty id")
        if case_id in seen:
            raise ValueError(f"duplicate eval case id: {case_id}")
        seen.add(case_id)
        if not isinstance(case.get("input"), str) or not case["input"].strip():
            raise ValueError(f"eval case '{case_id}' requires non-empty input")
        expected = case.get("expected")
        if not isinstance(expected, dict):
            raise ValueError(f"eval case '{case_id}' requires expected object")
        if "suggested_action" not in expected:
            raise ValueError(f"eval case '{case_id}' requires expected action")
        if not isinstance(expected.get("arguments"), dict):
            raise ValueError(f"eval case '{case_id}' requires expected arguments")
        if not isinstance(expected.get("valid_contract"), bool):
            raise ValueError(f"eval case '{case_id}' requires expected valid_contract")

    return payload


def run_suite(
    *,
    models: list[str],
    backends: list[str],
    cases_path: Path = DEFAULT_CASES_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    model_router: ModelRouter | None = None,
    tool_registry: ToolRegistry = production_registry,
    write_result: bool = True,
    timestamp: str | None = None,
) -> dict[str, Any]:
    cases_payload = load_eval_cases(cases_path)
    router = model_router or ModelRouter()
    created_at = datetime.now(timezone.utc).isoformat()
    artifact_timestamp = timestamp or datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S"
    )

    model_results = [
        evaluate_model_backend(
            model=model,
            backend=backend,
            cases=cases_payload["cases"],
            model_router=router,
            tool_registry=tool_registry,
        )
        for backend in backends
        for model in models
    ]
    ranking = sorted(
        [ranking_item(result) for result in model_results],
        key=lambda item: (
            item["runtime_candidate"],
            item["score"],
            item["valid_contract_rate"],
        ),
        reverse=True,
    )

    artifact = {
        "version": EVAL_VERSION,
        "created_at": created_at,
        "cases_version": cases_payload["version"],
        "criteria": {
            "runtime_candidate_min_valid_contract_rate": (
                RUNTIME_CANDIDATE_MIN_VALID_CONTRACT_RATE
            ),
            "runtime_candidate_max_fallback_rate": (
                RUNTIME_CANDIDATE_MAX_FALLBACK_RATE
            ),
        },
        "models": models,
        "backends": backends,
        "results": model_results,
        "ranking": ranking,
    }

    if write_result:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"agent_proposal_eval_{artifact_timestamp}.json"
        output_path.write_text(
            json.dumps(artifact, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact["output_path"] = str(output_path)

    return artifact


def evaluate_model_backend(
    *,
    model: str,
    backend: str,
    cases: list[dict[str, Any]],
    model_router: ModelRouter,
    tool_registry: ToolRegistry = production_registry,
) -> dict[str, Any]:
    case_results = [
        evaluate_case(
            case=case,
            model=model,
            backend=backend,
            model_router=model_router,
            tool_registry=tool_registry,
        )
        for case in cases
    ]
    metrics = summarize_case_results(case_results)
    return {
        "model": model,
        "backend": backend,
        **metrics,
        "cases": case_results,
    }


def evaluate_case(
    *,
    case: dict[str, Any],
    model: str,
    backend: str,
    model_router: ModelRouter,
    tool_registry: ToolRegistry = production_registry,
) -> dict[str, Any]:
    expected = case["expected"]
    try:
        request = AgentRequest(
            user_input=case["input"],
            options=AgentRunOptions(
                backend=AgentBackend(backend),
                model_id=model,
                agent_mode="proposal_only",
                dry_run=True,
            ),
        )
        provider = ModelRouterProposalProvider(
            model_router=model_router,
            tool_registry=tool_registry,
        )
        llm_input = LLMAssistedPlannerStrategy._build_llm_input(request)
        router_result = provider(llm_input, request)
    except Exception as exc:
        return _error_case_result(case, model, backend, str(exc))

    raw_output = _string_value(router_result.get("output"))
    valid_json, decoded_output, json_error = parse_model_json(raw_output)
    valid_contract = False
    contract_error: str | None = None
    proposal = proposal_from_decoded(decoded_output)

    if valid_json:
        try:
            validated = LLMPlanOutputValidator(tool_registry).validate_raw_output(
                raw_output
            )
            valid_contract = True
            proposal = {
                "intent": validated.intent,
                "suggested_action": validated.suggested_action,
                "arguments": validated.arguments,
                "confidence": validated.confidence,
            }
        except Exception as exc:
            contract_error = str(exc)
    else:
        contract_error = json_error

    action_match = (
        proposal is not None
        and proposal.get("suggested_action") == expected["suggested_action"]
    )
    arguments_match = (
        proposal is not None and proposal.get("arguments") == expected["arguments"]
    )
    provider_unavailable = is_provider_unavailable(router_result)
    router_fallback_used = bool(router_result.get("fallback_used"))
    fallback_used = router_fallback_used or not valid_contract
    fallback_reason = _fallback_reason(
        router_result=router_result,
        contract_error=contract_error,
        fallback_used=fallback_used,
    )

    return {
        "case_id": case["id"],
        "input": case["input"],
        "model": model,
        "backend": backend,
        "model_used": router_result.get("model_used"),
        "backend_used": router_result.get("backend_used"),
        "raw_output": raw_output,
        "proposal": proposal,
        "valid_json": valid_json,
        "valid_contract": valid_contract,
        "expected_valid_contract": expected["valid_contract"],
        "expected_action_match": action_match,
        "expected_arguments_match": arguments_match,
        "fallback_used": fallback_used,
        "router_fallback_used": router_fallback_used,
        "fallback_reason": fallback_reason,
        "latency_ms": _float_value(router_result.get("latency_ms")),
        "provider_unavailable": provider_unavailable,
        "critical_failure": False,
        "error": contract_error,
    }


def parse_model_json(raw_output: str) -> tuple[bool, object | None, str | None]:
    try:
        return True, json.loads(_strip_json_fence(raw_output)), None
    except Exception as exc:
        return False, None, str(exc)


def proposal_from_decoded(decoded_output: object | None) -> dict[str, Any] | None:
    if not isinstance(decoded_output, dict):
        return None

    arguments = decoded_output.get("arguments")
    return {
        "intent": decoded_output.get("intent"),
        "suggested_action": decoded_output.get("suggested_action"),
        "arguments": arguments if isinstance(arguments, dict) else None,
        "confidence": decoded_output.get("confidence"),
    }


def summarize_case_results(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    scored_cases = [
        result for result in case_results if not result["provider_unavailable"]
    ]
    provider_unavailable = bool(case_results) and not scored_cases
    denominator = len(scored_cases)
    critical_failures = [
        result["case_id"] for result in case_results if result["critical_failure"]
    ]

    valid_json_rate = _rate(scored_cases, "valid_json")
    valid_contract_rate = _rate(scored_cases, "valid_contract")
    expected_action_match_rate = _rate(scored_cases, "expected_action_match")
    expected_arguments_match_rate = _rate(scored_cases, "expected_arguments_match")
    fallback_rate = _rate(scored_cases, "fallback_used") if denominator else 1.0
    avg_latency_ms = _avg_latency(scored_cases)
    score = round(
        (
            valid_json_rate
            + valid_contract_rate
            + expected_action_match_rate
            + expected_arguments_match_rate
        )
        / 4,
        4,
    )
    runtime_candidate = (
        not provider_unavailable
        and not critical_failures
        and valid_contract_rate >= RUNTIME_CANDIDATE_MIN_VALID_CONTRACT_RATE
        and fallback_rate <= RUNTIME_CANDIDATE_MAX_FALLBACK_RATE
    )

    return {
        "score": score,
        "valid_json_rate": valid_json_rate,
        "valid_contract_rate": valid_contract_rate,
        "expected_action_match_rate": expected_action_match_rate,
        "expected_arguments_match_rate": expected_arguments_match_rate,
        "fallback_rate": fallback_rate,
        "avg_latency_ms": avg_latency_ms,
        "provider_unavailable": provider_unavailable,
        "critical_failures": critical_failures,
        "runtime_candidate": runtime_candidate,
    }


def ranking_item(model_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model_result["model"],
        "backend": model_result["backend"],
        "score": model_result["score"],
        "valid_contract_rate": model_result["valid_contract_rate"],
        "fallback_rate": model_result["fallback_rate"],
        "avg_latency_ms": model_result["avg_latency_ms"],
        "runtime_candidate": model_result["runtime_candidate"],
        "provider_unavailable": model_result["provider_unavailable"],
        "critical_failures": model_result["critical_failures"],
    }


def is_provider_unavailable(router_result: dict[str, Any]) -> bool:
    output = _string_value(router_result.get("output")).strip()
    reason = _string_value(router_result.get("fallback_reason")).lower()
    markers = (
        "not configured",
        "not available",
        "unavailable",
        "model_not_available",
        "connection",
        "refused",
    )
    return not output and bool(reason) and any(marker in reason for marker in markers)


def _fallback_reason(
    *,
    router_result: dict[str, Any],
    contract_error: str | None,
    fallback_used: bool,
) -> str | None:
    router_reason = router_result.get("fallback_reason")
    if isinstance(router_reason, str) and router_reason:
        if contract_error:
            return f"{router_reason}; {contract_error}"
        return router_reason
    if fallback_used:
        return contract_error or "deterministic fallback would be required"
    return None


def _error_case_result(
    case: dict[str, Any],
    model: str,
    backend: str,
    error: str,
) -> dict[str, Any]:
    return {
        "case_id": case.get("id"),
        "input": case.get("input"),
        "model": model,
        "backend": backend,
        "model_used": model,
        "backend_used": backend,
        "raw_output": "",
        "proposal": None,
        "valid_json": False,
        "valid_contract": False,
        "expected_valid_contract": case.get("expected", {}).get("valid_contract"),
        "expected_action_match": False,
        "expected_arguments_match": False,
        "fallback_used": True,
        "router_fallback_used": False,
        "fallback_reason": error,
        "latency_ms": 0.0,
        "provider_unavailable": False,
        "critical_failure": True,
        "error": error,
    }


def _rate(results: list[dict[str, Any]], field: str) -> float:
    if not results:
        return 0.0
    return round(sum(1 for result in results if result[field]) / len(results), 4)


def _avg_latency(results: list[dict[str, Any]]) -> float:
    if not results:
        return 0.0
    return round(
        sum(_float_value(result.get("latency_ms")) for result in results)
        / len(results),
        3,
    )


def _float_value(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _string_value(value: object) -> str:
    return value if isinstance(value, str) else ""


def _csv_values(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run NUCLEO agent proposal contract evals."
    )
    parser.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="Comma-separated model IDs.",
    )
    parser.add_argument(
        "--backends",
        default=",".join(DEFAULT_BACKENDS),
        help="Comma-separated backends: local, openai, auto.",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Path to eval cases JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where result JSON is written.",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=DEFAULT_TIMEOUT_MS,
        help="Model call timeout in milliseconds.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    models = _csv_values(args.models)
    backends = _csv_values(args.backends)
    if not models:
        raise SystemExit("--models must contain at least one model")
    if not backends:
        raise SystemExit("--backends must contain at least one backend")

    artifact = run_suite(
        models=models,
        backends=backends,
        cases_path=args.cases,
        output_dir=args.output_dir,
        model_router=ModelRouter(timeout_ms=args.timeout_ms),
    )

    print(json.dumps({"output_path": artifact["output_path"]}, indent=2))
    print(json.dumps({"ranking": artifact["ranking"]}, indent=2))


if __name__ == "__main__":
    main()
