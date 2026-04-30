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
from typing import Any

from .build_index import build_index, write_index
from .search import search


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
