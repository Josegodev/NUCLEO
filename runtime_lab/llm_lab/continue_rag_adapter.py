"""Continue adapter for local NUCLEO RAG evidence.

This module only prepares prompts from evidence returned by the local
nucleo_rag_api endpoint. It does not call LLMs, import NUCLEO runtime
components, register tools, or execute tools.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests


DEFAULT_ENDPOINT = "http://127.0.0.1:9000/nucleo-rag/query"
DEFAULT_TIMEOUT_SECONDS = 5

EVIDENCE_FOUND = "EVIDENCE_FOUND"
EVIDENCE_NOT_FOUND = "EVIDENCE_NOT_FOUND"
ERROR = "ERROR"
ALLOWED_STATUSES = {EVIDENCE_FOUND, EVIDENCE_NOT_FOUND, ERROR}


def build_continue_rag_prompt(
    query: str,
    top_k: int = 5,
    endpoint: str = DEFAULT_ENDPOINT,
) -> dict[str, Any]:
    """Build a Continue-ready prompt from the local RAG HTTP endpoint."""
    cleaned_query = _clean_query(query)
    if cleaned_query is None:
        return _result(ERROR, "", [], "INVALID_QUERY")

    if not _valid_top_k(top_k):
        return _result(ERROR, "", [], "INVALID_TOP_K")

    cleaned_endpoint = endpoint.strip() if isinstance(endpoint, str) else ""
    if not cleaned_endpoint:
        return _result(ERROR, "", [], "INVALID_ENDPOINT")

    payload = {
        "query": cleaned_query,
        "top_k": top_k,
    }

    try:
        response = requests.post(
            cleaned_endpoint,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout:
        return _result(ERROR, "", [], "RAG_ENDPOINT_TIMEOUT")
    except requests.exceptions.ConnectionError:
        return _result(ERROR, "", [], "RAG_ENDPOINT_UNAVAILABLE")
    except requests.exceptions.RequestException:
        return _result(ERROR, "", [], "RAG_ENDPOINT_REQUEST_FAILED")

    try:
        response_payload = response.json()
    except ValueError:
        return _result(ERROR, "", [], "RAG_ENDPOINT_INVALID_JSON")

    if not isinstance(response_payload, dict):
        return _result(ERROR, "", [], "RAG_ENDPOINT_INVALID_RESPONSE")

    if not _response_ok(response):
        endpoint_error = _safe_error(response_payload)
        error = f"RAG_ENDPOINT_HTTP_{response.status_code}"
        if endpoint_error:
            error = f"{error}: {endpoint_error}"
        return _result(ERROR, "", [], error)

    status = str(response_payload.get("status", ""))
    evidence = _normalize_evidence(response_payload.get("evidence", []))
    endpoint_error = _safe_error(response_payload)

    if status == EVIDENCE_FOUND:
        if not evidence:
            return _result(ERROR, "", [], "RAG_EMPTY_EVIDENCE")
        return _result(EVIDENCE_FOUND, _build_prompt(cleaned_query, evidence), evidence, None)

    if status == EVIDENCE_NOT_FOUND:
        return _result(EVIDENCE_NOT_FOUND, "", [], None)

    if status == ERROR:
        return _result(ERROR, "", [], endpoint_error or "RAG_ENDPOINT_ERROR")

    return _result(ERROR, "", [], "RAG_ENDPOINT_UNKNOWN_STATUS")


def _clean_query(query: str) -> str | None:
    if not isinstance(query, str):
        return None
    cleaned = query.strip()
    return cleaned or None


def _valid_top_k(top_k: int) -> bool:
    return isinstance(top_k, int) and not isinstance(top_k, bool) and 1 <= top_k <= 10


def _response_ok(response: requests.Response) -> bool:
    return 200 <= int(response.status_code) < 300


def _safe_error(payload: dict[str, Any]) -> str | None:
    error = payload.get("error")
    if error is None:
        return None
    error_text = str(error).strip()
    return error_text or None


def _normalize_evidence(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    evidence: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue

        text = str(item.get("text", "")).strip()
        source = str(item.get("source", "")).strip()
        if not text or not source:
            continue

        evidence.append(
            {
                "text": text,
                "source": source,
                "score": _safe_score(item.get("score")),
            }
        )
    return evidence


def _safe_score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _build_prompt(query: str, evidence: list[dict[str, Any]]) -> str:
    evidence_blocks = []
    for index, item in enumerate(evidence, start=1):
        evidence_blocks.append(
            "\n".join(
                [
                    f"[{index}] source={item['source']} score={item['score']}",
                    item["text"],
                ]
            )
        )

    return "\n".join(
        [
            "INSTRUCCIONES:",
            "- Responde solo usando la evidencia.",
            "- Si la evidencia no basta, di EVIDENCE_NOT_FOUND.",
            "- No inventes rutas, contratos, clases ni comportamiento.",
            "- No propongas cambios fuera del alcance preguntado.",
            "",
            "PREGUNTA:",
            query,
            "",
            "EVIDENCIA:",
            "\n\n".join(evidence_blocks),
        ]
    )


def _result(
    status: str,
    prompt: str,
    evidence: list[dict[str, Any]],
    error: str | None,
) -> dict[str, Any]:
    if status not in ALLOWED_STATUSES:
        status = ERROR
        prompt = ""
        evidence = []
        error = error or "INVALID_STATUS"

    return {
        "status": status,
        "prompt": prompt,
        "evidence": evidence,
        "error": error,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Continue-ready prompt from local NUCLEO RAG evidence"
    )
    parser.add_argument("query", help="Question to enrich with local RAG evidence")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_continue_rag_prompt(
        query=args.query,
        top_k=args.top_k,
        endpoint=args.endpoint,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
