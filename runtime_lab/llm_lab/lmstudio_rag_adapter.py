"""LM Studio adapter for local NUCLEO RAG evidence.

This module is experimental llm_lab code. It keeps the flow closed:
query -> deterministic RAG retrieval -> prompt with evidence -> LM Studio.
It does not import NUCLEO runtime components, policies, registries, or tools.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from runtime_lab.llm_lab.rag_nucleo_docs.search import search as rag_search


OK = "OK"
NO_EVIDENCE = "NO_EVIDENCE"
LMSTUDIO_UNAVAILABLE = "LMSTUDIO_UNAVAILABLE"
ERROR = "ERROR"

DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1"
DEFAULT_MODEL = "qwen/qwen3.5-9b"
DEFAULT_TOP_K = 5
DEFAULT_MAX_CONTEXT_CHARS = 8000
DEFAULT_TIMEOUT_SECONDS = 20
SYSTEM_PROMPT = (
    "You answer only using the provided evidence. If the answer is not present "
    "in the evidence, answer exactly NO_EVIDENCE. Every factual claim must cite "
    "evidence markers like [E1]. Do not use prior knowledge."
)
TRACE_LOG_PATH = (
    Path(__file__).resolve().parent / "logs" / "lmstudio_rag_trace.jsonl"
)
CITATION_RE = re.compile(r"\[E([0-9]+)\]")


class LMStudioUnavailableError(RuntimeError):
    """Raised when the LM Studio endpoint cannot answer deterministically."""


class LMStudioClientError(RuntimeError):
    """Raised when LM Studio returns a 4xx response."""


class LMStudioMalformedResponseError(RuntimeError):
    """Raised when LM Studio returns an unexpected response shape."""


def answer_with_lmstudio_rag(
    query: str,
    top_k: int | None = None,
) -> dict[str, Any]:
    """Answer a query using only evidence recovered by rag_nucleo_docs."""
    cleaned_query = _clean_query(query)
    resolved_top_k = _resolve_top_k(top_k)
    model = _env_text("LMSTUDIO_MODEL", DEFAULT_MODEL)
    base_url = _env_text("LMSTUDIO_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    max_context_chars = _env_positive_int(
        "RAG_MAX_CONTEXT_CHARS",
        DEFAULT_MAX_CONTEXT_CHARS,
    )
    timeout_seconds = _env_positive_int(
        "LMSTUDIO_TIMEOUT_SECONDS",
        DEFAULT_TIMEOUT_SECONDS,
    )
    trace = _trace(cleaned_query or str(query), resolved_top_k, model, base_url, None)

    if cleaned_query is None:
        return _final_result(
            status=ERROR,
            answer=None,
            evidence=[],
            trace={**trace, "fallback_reason": "INVALID_QUERY"},
        )

    if resolved_top_k < 1:
        return _final_result(
            status=ERROR,
            answer=None,
            evidence=[],
            trace={**trace, "fallback_reason": "INVALID_TOP_K"},
        )

    try:
        retrieval = rag_search(cleaned_query, top_k=resolved_top_k)
        raw_results = retrieval.get("results", []) if isinstance(retrieval, dict) else []
        evidence = _prepare_evidence(raw_results, max_context_chars)
    except FileNotFoundError:
        return _final_result(
            status=ERROR,
            answer=None,
            evidence=[],
            trace={**trace, "fallback_reason": "RAG_INDEX_NOT_FOUND"},
        )
    except Exception:
        return _final_result(
            status=ERROR,
            answer=None,
            evidence=[],
            trace={**trace, "fallback_reason": "RAG_RETRIEVAL_FAILED"},
        )

    if not evidence:
        return _final_result(
            status=NO_EVIDENCE,
            answer=NO_EVIDENCE,
            evidence=[],
            trace={**trace, "fallback_reason": NO_EVIDENCE},
        )

    try:
        model_ids = _get_lmstudio_model_ids(base_url, timeout_seconds)
    except LMStudioUnavailableError:
        return _final_result(
            status=LMSTUDIO_UNAVAILABLE,
            answer=LMSTUDIO_UNAVAILABLE,
            evidence=evidence,
            trace={**trace, "fallback_reason": "models_endpoint_unavailable"},
        )
    except LMStudioClientError:
        return _final_result(
            status=ERROR,
            answer=None,
            evidence=evidence,
            trace={**trace, "fallback_reason": "models_endpoint_error"},
        )
    except Exception:
        return _final_result(
            status=ERROR,
            answer=None,
            evidence=evidence,
            trace={**trace, "fallback_reason": "models_endpoint_invalid_response"},
        )

    if model not in model_ids:
        return _final_result(
            status=ERROR,
            answer=None,
            evidence=evidence,
            trace={**trace, "fallback_reason": "model_not_loaded"},
        )

    messages = _build_messages(cleaned_query, evidence)
    prompt_hash = _hash_json(messages)
    try:
        answer = _call_lmstudio_chat(
            model=model,
            base_url=base_url,
            messages=messages,
            timeout_seconds=timeout_seconds,
        )
    except LMStudioUnavailableError:
        return _final_result(
            status=LMSTUDIO_UNAVAILABLE,
            answer=LMSTUDIO_UNAVAILABLE,
            evidence=evidence,
            trace={**trace, "fallback_reason": "chat_endpoint_unavailable"},
            prompt_hash=prompt_hash,
            response_hash=_hash_text(LMSTUDIO_UNAVAILABLE),
        )
    except LMStudioClientError:
        return _final_result(
            status=ERROR,
            answer=None,
            evidence=evidence,
            trace={**trace, "fallback_reason": "chat_endpoint_error"},
            prompt_hash=prompt_hash,
        )
    except Exception:
        return _final_result(
            status=ERROR,
            answer=None,
            evidence=evidence,
            trace={**trace, "fallback_reason": "LMSTUDIO_REQUEST_FAILED"},
            prompt_hash=prompt_hash,
        )

    response_hash = _hash_text(answer)
    if answer == NO_EVIDENCE:
        return _final_result(
            status=NO_EVIDENCE,
            answer=NO_EVIDENCE,
            evidence=evidence,
            trace={**trace, "fallback_reason": NO_EVIDENCE},
            prompt_hash=prompt_hash,
            response_hash=response_hash,
        )

    validation_error = _validate_answer_citations(answer, evidence)
    if validation_error is not None:
        return _final_result(
            status=ERROR,
            answer=None,
            evidence=evidence,
            trace={**trace, "fallback_reason": validation_error},
            prompt_hash=prompt_hash,
            response_hash=response_hash,
        )

    return _final_result(
        status=OK,
        answer=answer,
        evidence=evidence,
        trace=trace,
        prompt_hash=prompt_hash,
        response_hash=response_hash,
    )


def _clean_query(query: str) -> str | None:
    if not isinstance(query, str):
        return None
    cleaned = query.strip()
    return cleaned or None


def _resolve_top_k(top_k: int | None) -> int:
    if top_k is not None:
        return _safe_int(top_k, fallback=0)
    return _env_positive_int("RAG_TOP_K", DEFAULT_TOP_K)


def _env_positive_int(name: str, default: int) -> int:
    value = os.getenv(name)
    parsed = _safe_int(value, fallback=default)
    return parsed if parsed > 0 else default


def _safe_int(value: Any, fallback: int) -> int:
    if isinstance(value, bool):
        return fallback
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _env_text(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    cleaned = value.strip()
    return cleaned or default


def _prepare_evidence(results: Any, max_context_chars: int) -> list[dict[str, Any]]:
    normalized = _normalize_evidence(results)
    limited = _apply_context_limit(normalized, max_context_chars)
    return _number_evidence(limited)


def _normalize_evidence(results: Any) -> list[dict[str, Any]]:
    if not isinstance(results, list):
        return []

    evidence: list[dict[str, Any]] = []
    for result in results:
        if not isinstance(result, dict):
            continue

        text = _evidence_text(result)
        if text is None:
            continue

        item: dict[str, Any] = {"text": text}
        for key in ("path", "file", "doc_id", "score"):
            if result.get(key) is not None:
                item[key] = result[key]

        line_start = result.get("line_start", result.get("start_line"))
        line_end = result.get("line_end", result.get("end_line"))
        if line_start is not None:
            item["line_start"] = line_start
        if line_end is not None:
            item["line_end"] = line_end

        evidence.append(item)

    return evidence


def _evidence_text(result: dict[str, Any]) -> str | None:
    for key in ("snippet", "content", "text"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _apply_context_limit(
    evidence: list[dict[str, Any]],
    max_context_chars: int,
) -> list[dict[str, Any]]:
    if max_context_chars < 1:
        return []

    remaining = max_context_chars
    limited: list[dict[str, Any]] = []
    for item in evidence:
        if remaining <= 0:
            break

        text = str(item.get("text", "")).strip()
        if not text:
            continue

        next_item = dict(item)
        if len(text) > remaining:
            text = _truncate_text(text, remaining)
            if not text:
                break
            next_item["truncated"] = True

        next_item["text"] = text
        limited.append(next_item)
        remaining -= len(text)

    return limited


def _truncate_text(text: str, limit: int) -> str:
    if limit < 1:
        return ""
    candidate = text[:limit].rstrip()
    if not candidate:
        return ""

    newline_index = candidate.rfind("\n")
    if newline_index >= max(1, limit // 2):
        return candidate[:newline_index].rstrip()

    space_index = candidate.rfind(" ")
    if space_index >= max(1, limit // 2):
        return candidate[:space_index].rstrip()

    return candidate


def _number_evidence(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numbered: list[dict[str, Any]] = []
    for index, item in enumerate(evidence, start=1):
        numbered_item = dict(item)
        numbered_item["id"] = f"E{index}"
        numbered.append(numbered_item)
    return numbered


def _build_messages(query: str, evidence: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(query, evidence)},
    ]


def _build_user_prompt(query: str, evidence: list[dict[str, Any]]) -> str:
    evidence_blocks = []
    for item in evidence:
        marker = item["id"]
        path = _evidence_path(item)
        score = item.get("score", "")
        evidence_blocks.append(
            "\n".join(
                [
                    f"[{marker}] path={path} score={score}",
                    item["text"],
                ]
            )
        )

    return "\n".join(
        [
            "Question:",
            query,
            "",
            "Instructions:",
            "Answer in Spanish.",
            "Use only the evidence below.",
            "Cite every factual claim with existing markers like [E1].",
            "If the evidence does not contain the answer, answer exactly NO_EVIDENCE.",
            "",
            "Evidence:",
            "\n\n".join(evidence_blocks),
        ]
    )


def _evidence_path(item: dict[str, Any]) -> str:
    value = item.get("path") or item.get("file") or item.get("doc_id") or "unknown"
    cleaned = str(value).strip()
    return cleaned or "unknown"


def _get_lmstudio_model_ids(base_url: str, timeout_seconds: int) -> set[str]:
    payload = _http_get_json(f"{base_url}/models", timeout_seconds)
    return _extract_model_ids(payload)


def _extract_model_ids(payload: Any) -> set[str]:
    if not isinstance(payload, dict):
        raise LMStudioMalformedResponseError("models response was not an object")

    raw_models = payload.get("data")
    if raw_models is None:
        raw_models = payload.get("models")
    if not isinstance(raw_models, list):
        raise LMStudioMalformedResponseError("models response did not include a list")

    model_ids: set[str] = set()
    for item in raw_models:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id") or item.get("name")
        if isinstance(model_id, str) and model_id.strip():
            model_ids.add(model_id.strip())

    return model_ids


def _call_lmstudio_chat(
    *,
    model: str,
    base_url: str,
    messages: list[dict[str, str]],
    timeout_seconds: int,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "stream": False,
    }
    response_payload = _http_post_json(
        f"{base_url}/chat/completions",
        payload,
        timeout_seconds,
    )
    return _extract_openai_compatible_answer(response_payload)


def _http_get_json(url: str, timeout_seconds: int) -> Any:
    try:
        import requests  # type: ignore[import-not-found]
    except ImportError:
        return _urllib_json("GET", url, None, timeout_seconds)

    try:
        response = requests.get(url, timeout=timeout_seconds)
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.RequestException,
    ) as exc:
        raise LMStudioUnavailableError("LM Studio is unavailable") from exc

    return _requests_json(response)


def _http_post_json(url: str, payload: dict[str, Any], timeout_seconds: int) -> Any:
    try:
        import requests  # type: ignore[import-not-found]
    except ImportError:
        return _urllib_json("POST", url, payload, timeout_seconds)

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=timeout_seconds,
        )
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.RequestException,
    ) as exc:
        raise LMStudioUnavailableError("LM Studio is unavailable") from exc

    return _requests_json(response)


def _requests_json(response: Any) -> Any:
    status_code = int(response.status_code)
    if 500 <= status_code:
        raise LMStudioUnavailableError("LM Studio returned a server error")
    if 400 <= status_code:
        raise LMStudioClientError("LM Studio returned a client error")

    try:
        return response.json()
    except ValueError as exc:
        raise LMStudioMalformedResponseError("LM Studio returned invalid JSON") from exc


def _urllib_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    timeout_seconds: int,
) -> Any:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib_request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        if 500 <= int(exc.code):
            raise LMStudioUnavailableError("LM Studio returned a server error") from exc
        raise LMStudioClientError("LM Studio returned a client error") from exc
    except (TimeoutError, urllib_error.URLError) as exc:
        raise LMStudioUnavailableError("LM Studio is unavailable") from exc
    except ValueError as exc:
        raise LMStudioMalformedResponseError("LM Studio returned invalid JSON") from exc


def _extract_openai_compatible_answer(payload: Any) -> str:
    if not isinstance(payload, dict):
        raise LMStudioMalformedResponseError("LM Studio response was not an object")

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LMStudioMalformedResponseError("LM Studio response did not include choices")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise LMStudioMalformedResponseError("LM Studio choice was not an object")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise LMStudioMalformedResponseError("LM Studio choice did not include message")

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LMStudioMalformedResponseError("LM Studio returned empty content")

    return content.strip()


def _validate_answer_citations(
    answer: str,
    evidence: list[dict[str, Any]],
) -> str | None:
    citations = {f"E{match}" for match in CITATION_RE.findall(answer)}
    if not citations:
        return "answer_not_grounded"

    valid_citations = {
        str(item.get("id"))
        for item in evidence
        if isinstance(item.get("id"), str)
    }
    if not citations <= valid_citations:
        return "invalid_evidence_citation"

    return None


def _trace(
    query: str,
    top_k: int,
    model: str,
    base_url: str,
    fallback_reason: str | None,
) -> dict[str, Any]:
    return {
        "query": query,
        "top_k": top_k,
        "model": model,
        "base_url": base_url,
        "fallback_reason": fallback_reason,
    }


def _final_result(
    *,
    status: str,
    answer: str | None,
    evidence: list[dict[str, Any]],
    trace: dict[str, Any],
    prompt_hash: str | None = None,
    response_hash: str | None = None,
) -> dict[str, Any]:
    result = {
        "status": status,
        "answer": answer,
        "evidence": evidence,
        "trace": trace,
    }
    _log_trace_if_enabled(
        result,
        prompt_hash=prompt_hash,
        response_hash=response_hash,
    )
    return result


def _log_trace_if_enabled(
    result: dict[str, Any],
    *,
    prompt_hash: str | None,
    response_hash: str | None,
) -> None:
    if os.getenv("LMSTUDIO_RAG_TRACE", "").strip() != "1":
        return

    trace = result.get("trace", {})
    if not isinstance(trace, dict):
        trace = {}

    log_record = {
        "query": trace.get("query"),
        "status": result.get("status"),
        "fallback_reason": trace.get("fallback_reason"),
        "model": trace.get("model"),
        "base_url": trace.get("base_url"),
        "top_k": trace.get("top_k"),
        "evidence": _evidence_log_refs(result.get("evidence", [])),
        "prompt_hash": prompt_hash,
        "response_hash": response_hash,
    }

    try:
        TRACE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with TRACE_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(log_record, ensure_ascii=False) + "\n")
    except OSError:
        return


def _evidence_log_refs(evidence: Any) -> list[dict[str, Any]]:
    if not isinstance(evidence, list):
        return []

    refs: list[dict[str, Any]] = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        refs.append(
            {
                "id": item.get("id"),
                "path": item.get("path") or item.get("file"),
                "doc_id": item.get("doc_id"),
                "score": item.get("score"),
            }
        )
    return refs


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
