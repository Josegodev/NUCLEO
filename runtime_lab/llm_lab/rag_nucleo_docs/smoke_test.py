"""Smoke tests for rag_nucleo_docs.

This script validates the experimental Markdown retrieval module without
touching NUCLEO runtime, app/, tools, or external dependencies.

Run from repo root:

    python3 -m runtime_lab.llm_lab.rag_nucleo_docs.smoke_test
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

from .build_index import build_index, write_index
from .query_index import query
from .rag_answer import build_answer


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def has_sources(result: dict[str, Any]) -> bool:
    return bool(result.get("sources"))


def answer_contains_any(result: dict[str, Any], terms: list[str]) -> bool:
    answer = str(result.get("answer", "")).lower()
    return any(term.lower() in answer for term in terms)


def warning_contains(result: dict[str, Any], expected: str) -> bool:
    warnings = result.get("warnings", [])
    return any(expected in str(warning) for warning in warnings)


def run_check(name: str, condition: bool, detail: str) -> CheckResult:
    return CheckResult(name=name, passed=condition, detail=detail)


def main() -> None:
    checks: list[CheckResult] = []

    # 1. Build index
    try:
        index = build_index()
        write_index(index)
        checks.append(
            run_check(
                "build_index",
                int(index.get("chunks_indexed", 0)) > 0,
                f"chunks_indexed={index.get('chunks_indexed')}",
            )
        )
    except Exception as exc:  # noqa: BLE001 - smoke test must report all failures
        checks.append(run_check("build_index", False, repr(exc)))

    # 2. Query dry_run
    try:
        dry_query = query("Qué hace dry_run=True?")
        checks.append(
            run_check(
                "query_dry_run_found",
                dry_query.get("status") == "FOUND"
                and bool(dry_query.get("results")),
                f"status={dry_query.get('status')}, results={len(dry_query.get('results', []))}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(run_check("query_dry_run_found", False, repr(exc)))

    # 3. Extractive answer must contain evidence
    try:
        dry_extractive = build_answer(
            "Qué hace dry_run=True?",
            mode="extractive",
        )
        checks.append(
            run_check(
                "extractive_dry_run_sources",
                has_sources(dry_extractive),
                f"sources={len(dry_extractive.get('sources', []))}",
            )
        )
        checks.append(
            run_check(
                "extractive_dry_run_contract_evidence",
                answer_contains_any(
                    dry_extractive,
                    ["tool.run", "executed=false", "executed=False"],
                ),
                "answer must mention tool.run or executed=false",
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(run_check("extractive_dry_run", False, repr(exc)))

    # 4. LLM mode must not return NO_CONSTA when retrieval found sources.
    # If model is unavailable or returns NO_CONSTA despite evidence, fallback is acceptable.
    try:
        dry_llm = build_answer(
            "Qué hace dry_run=True?",
            mode="llm",
        )
        checks.append(
            run_check(
                "llm_dry_run_sources",
                has_sources(dry_llm),
                f"sources={len(dry_llm.get('sources', []))}",
            )
        )
        checks.append(
            run_check(
                "llm_dry_run_not_false_no_consta",
                dry_llm.get("answer") != "NO_CONSTA_EN_DOCUMENTACION",
                "answer must not be NO_CONSTA when sources exist",
            )
        )
        checks.append(
            run_check(
                "llm_dry_run_contract_evidence",
                answer_contains_any(
                    dry_llm,
                    ["tool.run", "executed=false", "executed=False"],
                ),
                "fallback or synthesis must preserve contract evidence",
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(run_check("llm_dry_run", False, repr(exc)))

    # 5. Negative query must return exact NO_CONSTA and no sources.
    try:
        negative = build_answer(
            "zxqv concepto inexistente 12345",
            mode="llm",
        )
        checks.append(
            run_check(
                "negative_no_consta_exact",
                negative.get("answer") == "NO_CONSTA_EN_DOCUMENTACION",
                f"answer={negative.get('answer')}",
            )
        )
        checks.append(
            run_check(
                "negative_sources_empty",
                negative.get("sources") == [],
                f"sources={negative.get('sources')}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(run_check("negative_query", False, repr(exc)))

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