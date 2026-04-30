"""Smoke tests for deterministic rag_nucleo_docs retrieval.

This script validates the experimental Markdown retrieval module without
touching NUCLEO runtime, app/, tools, LLMs, or external dependencies.

Run from repo root:

    python3 -m runtime_lab.llm_lab.rag_nucleo_docs.smoke_test
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .build_index import build_index, normalize_text, write_index
from .search import search


EVAL_CASES_FILE = Path(__file__).with_name("eval_cases.json")
EXPECTED_EVAL_VERSION = "rag_eval.v1"
EXPECTED_EVAL_TARGET = "retrieval"
REQUIRED_RESULT_FIELDS = {"doc_id", "score", "snippet"}


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def run_check(name: str, condition: bool, detail: str) -> CheckResult:
    return CheckResult(name=name, passed=condition, detail=detail)


def result_has_required_fields(result: dict[str, Any]) -> bool:
    """Return True when a search result satisfies the public minimum contract."""
    return REQUIRED_RESULT_FIELDS <= set(result)


def all_results_have_required_fields(results: list[dict[str, Any]]) -> bool:
    return all(result_has_required_fields(result) for result in results)


def load_eval_suite() -> dict[str, Any]:
    """Load the declarative retrieval evaluation suite."""
    return json.loads(EVAL_CASES_FILE.read_text(encoding="utf-8"))


def is_int(value: Any) -> bool:
    """Return True only for real integers, not booleans."""
    return isinstance(value, int) and not isinstance(value, bool)


def require_string_list(value: Any) -> list[str] | None:
    """Return a string list, or None when the schema is invalid."""
    if not isinstance(value, list):
        return None
    if not all(isinstance(item, str) for item in value):
        return None
    return value


def retrieved_text(results: list[dict[str, Any]]) -> str:
    """Concatenate retrieved evidence text for term checks."""
    parts = []
    for result in results:
        parts.append(str(result.get("snippet") or result.get("text") or ""))
    return "\n".join(parts)


def retrieved_sources(results: list[dict[str, Any]]) -> list[str]:
    """Return source identifiers available on retrieval results."""
    sources = []
    for result in results:
        sources.append(str(result.get("file", "")))
        sources.append(str(result.get("doc_id", "")))
    return sources


def normalized_contains(text: str, term: str, *, whole_term: bool) -> bool:
    """Match a term after deterministic lexical normalization."""
    normalized_text = normalize_text(text)
    normalized_term = normalize_text(term)
    if not normalized_term:
        return False
    if not whole_term:
        return normalized_term in normalized_text
    return f" {normalized_term} " in f" {normalized_text} "


def run_eval_case(index: int, case: Any) -> list[CheckResult]:
    """Validate one eval case against the public search() contract."""
    if not isinstance(case, dict):
        return [
            run_check(
                f"eval.case_{index}.schema",
                False,
                "case must be an object",
            )
        ]

    case_id = str(case.get("id", f"case_{index}"))
    checks: list[CheckResult] = []
    question = case.get("question")
    if not isinstance(question, str) or not question.strip():
        return [
            run_check(
                f"eval.{case_id}.question",
                False,
                "question must be a non-empty string",
            )
        ]

    first = search(question, top_k=5)
    second = search(question, top_k=5)
    checks.append(
        run_check(
            f"eval.{case_id}.deterministic",
            first == second,
            "two identical search() calls must return exactly the same payload",
        )
    )

    raw_results = first.get("results")
    results_are_list = isinstance(raw_results, list)
    checks.append(
        run_check(
            f"eval.{case_id}.results_list",
            results_are_list,
            "results must exist and be a list",
        )
    )
    if not results_are_list:
        return checks

    results = raw_results
    results_are_objects = all(isinstance(result, dict) for result in results)
    checks.append(
        run_check(
            f"eval.{case_id}.results_objects",
            results_are_objects,
            "every result must be an object",
        )
    )
    if not results_are_objects:
        return checks

    checks.append(
        run_check(
            f"eval.{case_id}.result_contract_fields",
            all_results_have_required_fields(results),
            f"every result must include {sorted(REQUIRED_RESULT_FIELDS)}",
        )
    )

    min_sources = case.get("min_sources", 0)
    checks.append(
        run_check(
            f"eval.{case_id}.min_sources_schema",
            is_int(min_sources),
            "min_sources must be an integer",
        )
    )
    if is_int(min_sources):
        checks.append(
            run_check(
                f"eval.{case_id}.min_sources",
                len(results) >= min_sources,
                f"expected at least {min_sources} results, got {len(results)}",
            )
        )

    if "expected_results" in case:
        expected_results = case["expected_results"]
        checks.append(
            run_check(
                f"eval.{case_id}.expected_results_schema",
                is_int(expected_results),
                "expected_results must be an integer",
            )
        )
        if is_int(expected_results):
            checks.append(
                run_check(
                    f"eval.{case_id}.expected_results",
                    len(results) == expected_results,
                    f"expected exactly {expected_results} results, got {len(results)}",
                )
            )

    evidence_text = retrieved_text(results)

    expected_terms = require_string_list(case.get("expected_terms", []))
    checks.append(
        run_check(
            f"eval.{case_id}.expected_terms_schema",
            expected_terms is not None,
            "expected_terms must be a list of strings",
        )
    )
    if expected_terms is not None:
        missing_terms = [
            term
            for term in expected_terms
            if not normalized_contains(evidence_text, term, whole_term=False)
        ]
        checks.append(
            run_check(
                f"eval.{case_id}.expected_terms",
                not missing_terms,
                f"missing expected terms: {missing_terms}",
            )
        )

    forbidden_terms = require_string_list(case.get("forbidden_terms", []))
    checks.append(
        run_check(
            f"eval.{case_id}.forbidden_terms_schema",
            forbidden_terms is not None,
            "forbidden_terms must be a list of strings",
        )
    )
    if forbidden_terms is not None:
        present_forbidden_terms = [
            term
            for term in forbidden_terms
            if normalized_contains(evidence_text, term, whole_term=True)
        ]
        checks.append(
            run_check(
                f"eval.{case_id}.forbidden_terms",
                not present_forbidden_terms,
                f"present forbidden terms: {present_forbidden_terms}",
            )
        )

    required_sources = require_string_list(case.get("required_sources", []))
    checks.append(
        run_check(
            f"eval.{case_id}.required_sources_schema",
            required_sources is not None,
            "required_sources must be a list of strings",
        )
    )
    if required_sources is not None:
        sources = retrieved_sources(results)
        missing_sources = [
            required
            for required in required_sources
            if not any(required in source for source in sources)
        ]
        checks.append(
            run_check(
                f"eval.{case_id}.required_sources",
                not missing_sources,
                f"missing required sources: {missing_sources}",
            )
        )

    return checks


def run_eval_suite() -> list[CheckResult]:
    """Validate eval_cases.json and execute every declared retrieval case."""
    checks: list[CheckResult] = []
    try:
        suite = load_eval_suite()
    except Exception as exc:  # noqa: BLE001 - smoke test must report failures
        return [run_check("eval.load", False, repr(exc))]

    if not isinstance(suite, dict):
        return [
            run_check(
                "eval.schema",
                False,
                "eval_cases.json must be an object with version, target, and cases",
            )
        ]

    checks.append(
        run_check(
            "eval.version",
            suite.get("version") == EXPECTED_EVAL_VERSION,
            f"version={suite.get('version')}",
        )
    )
    checks.append(
        run_check(
            "eval.target",
            suite.get("target") == EXPECTED_EVAL_TARGET,
            f"target={suite.get('target')}",
        )
    )

    cases = suite.get("cases")
    cases_are_list = isinstance(cases, list)
    checks.append(
        run_check(
            "eval.cases_schema",
            cases_are_list,
            "cases must be a list",
        )
    )
    if not cases_are_list:
        return checks

    for index, case in enumerate(cases, start=1):
        try:
            checks.extend(run_eval_case(index, case))
        except Exception as exc:  # noqa: BLE001 - keep reporting all case failures
            case_id = (
                case.get("id", f"case_{index}")
                if isinstance(case, dict)
                else f"case_{index}"
            )
            checks.append(run_check(f"eval.{case_id}.exception", False, repr(exc)))

    return checks


def main() -> None:
    checks: list[CheckResult] = []

    try:
        index = build_index()
        write_index(index)
        chunks_indexed = len(index.get("chunks", []))
        checks.append(
            run_check(
                "build_index",
                chunks_indexed > 0,
                f"chunks_indexed={chunks_indexed}",
            )
        )
    except Exception as exc:  # noqa: BLE001 - smoke test must report all failures
        checks.append(run_check("build_index", False, repr(exc)))

    query_text = "Qué hace dry_run=True?"

    try:
        first = search(query_text, top_k=5)
        second = search(query_text, top_k=5)
        checks.append(
            run_check(
                "search_dry_run_found",
                first.get("status") == "FOUND" and bool(first.get("results")),
                f"status={first.get('status')}, results={len(first.get('results', []))}",
            )
        )
        checks.append(
            run_check(
                "search_deterministic_exact_output",
                first == second,
                "two identical searches must return exactly the same payload",
            )
        )
        results = list(first.get("results", []))
        checks.append(
            run_check(
                "search_result_contract_fields",
                all_results_have_required_fields(results),
                f"required={sorted(REQUIRED_RESULT_FIELDS)}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(run_check("search_contract", False, repr(exc)))

    try:
        top_1 = search(query_text, top_k=1)
        top_3 = search(query_text, top_k=3)
        checks.append(
            run_check(
                "search_top_k_size",
                len(top_1.get("results", [])) <= 1
                and len(top_3.get("results", [])) <= 3,
                (
                    f"top_1={len(top_1.get('results', []))}, "
                    f"top_3={len(top_3.get('results', []))}"
                ),
            )
        )
        checks.append(
            run_check(
                "search_top_k_stable_prefix",
                top_1.get("results", []) == top_3.get("results", [])[:1],
                "top_k=1 must be the first result of top_k=3",
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(run_check("search_top_k", False, repr(exc)))

    checks.extend(run_eval_suite())

    passed = all(check.passed for check in checks)

    payload = {
        "status": "passed" if passed else "failed",
        "checks": [check.__dict__ for check in checks],
    }

    print(json.dumps(payload, indent=2, ensure_ascii=False))

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
