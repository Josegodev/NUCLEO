"""Evidence packaging for deterministic rag_nucleo_docs retrieval.

This module is an experimental llm_lab boundary. It does not import or call
NUCLEO runtime components, and it never executes tools.
"""

from __future__ import annotations

from typing import Any

from .config import DEFAULT_TOP_K
from .search import search


EVIDENCE_FOUND = "EVIDENCE_FOUND"
NO_EVIDENCE = "NO_EVIDENCE"
NO_EVIDENCE_ANSWER = "NO_CONSTA_EN_DOCUMENTACION"


def build_evidence_item(result: dict[str, object]) -> dict[str, Any]:
    """Build one evidence item using the existing evidence.py contract."""
    return {
        "doc_id": result.get("doc_id"),
        "source": result.get("file") or result.get("doc_id"),
        "score": result.get("score"),
        "snippet": result.get("snippet"),
    }


def build_evidence_package(query: str, top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    """Build a deterministic evidence package from search()."""
    retrieval = search(query, top_k=top_k)
    raw_results = retrieval.get("results", [])
    results = raw_results if isinstance(raw_results, list) else []
    evidence = [
        build_evidence_item(result)
        for result in results
        if isinstance(result, dict)
    ]
    status = EVIDENCE_FOUND if evidence else NO_EVIDENCE

    return {
        "query": query,
        "evidence": evidence,
        "status": status,
    }
