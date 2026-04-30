"""Build extractive RAG answers from a closed evidence package.

This module belongs to runtime_lab/llm_lab. It does not import or call NUCLEO
runtime components, and it never executes tools.
"""

from __future__ import annotations

import argparse
import json

from .config import DEFAULT_TOP_K
from .evidence import (
    EVIDENCE_FOUND,
    NO_EVIDENCE,
    NO_EVIDENCE_ANSWER,
    build_evidence_package,
)


def build_answer_from_evidence(
    evidence_package: dict[str, object],
) -> dict[str, object]:
    """Build a structured answer using only evidence package snippets."""
    query = str(evidence_package.get("query", ""))
    status = str(evidence_package.get("status", NO_EVIDENCE))
    evidence = list(evidence_package.get("evidence", []))

    if status == NO_EVIDENCE:
        answer = NO_EVIDENCE_ANSWER
    elif status == EVIDENCE_FOUND:
        snippets = [
            str(item.get("snippet", "")).strip()
            for item in evidence
            if isinstance(item, dict) and str(item.get("snippet", "")).strip()
        ]
        answer = "\n\n".join(snippets)
    else:
        raise ValueError(f"Unsupported evidence status: {status}")

    return {
        "query": query,
        "status": status,
        "answer": answer,
        "evidence": evidence,
    }


def build_answer(
    query: str,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, object]:
    """Build an extractive answer from deterministic retrieval evidence."""
    evidence_package = build_evidence_package(query, top_k=top_k)
    return build_answer_from_evidence(evidence_package)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Answer using deterministic NUCLEO Markdown evidence"
    )
    parser.add_argument("query", help="Question to answer from documentation")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_answer(args.query, top_k=args.top_k)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
