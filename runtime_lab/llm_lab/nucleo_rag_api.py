"""HTTP API for deterministic NUCLEO documentation retrieval.

This module belongs to runtime_lab/llm_lab only. It exposes existing
rag_nucleo_docs retrieval as read-only evidence and does not call LLMs,
NUCLEO runtime components, policies, registries, or tools.
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from runtime_lab.llm_lab.rag_nucleo_docs.search import search as rag_search


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTEXT_TOP_K = 5
logger = logging.getLogger(__name__)


class RagStatus(str, Enum):
    EVIDENCE_FOUND = "EVIDENCE_FOUND"
    EVIDENCE_NOT_FOUND = "EVIDENCE_NOT_FOUND"
    ERROR = "ERROR"


class RagQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value


class EvidenceItem(BaseModel):
    text: str
    source: str
    score: float = 0.0


class RagQueryResponse(BaseModel):
    status: RagStatus
    evidence: list[EvidenceItem] = Field(default_factory=list)
    error: str | None = None


class ContinueContextRequest(BaseModel):
    query: Any = None
    fullInput: Any = None
    options: Any = None


class ContinueContextItem(BaseModel):
    name: str
    description: str
    content: str


app = FastAPI(title="NUCLEO RAG Evidence API")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return _error_response("INVALID_REQUEST: " + _validation_error_message(exc), 422)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "nucleo_rag_api",
    }


@app.post("/nucleo-rag/query", response_model=RagQueryResponse)
async def query_rag(request: RagQueryRequest) -> RagQueryResponse | JSONResponse:
    try:
        retrieval = rag_search(request.query, top_k=request.top_k)
        if not isinstance(retrieval, dict):
            return _error_response("RAG_INVALID_RESPONSE", 500)
        evidence = _normalize_evidence(retrieval.get("results", []))
    except FileNotFoundError:
        return _error_response("RAG_INDEX_NOT_FOUND", 503)
    except ValueError as exc:
        return _error_response(str(exc), 400)
    except Exception:
        return _error_response("RAG_QUERY_FAILED", 500)

    status = RagStatus.EVIDENCE_FOUND if evidence else RagStatus.EVIDENCE_NOT_FOUND
    return RagQueryResponse(status=status, evidence=evidence, error=None)


@app.post("/nucleo-rag/context", response_model=list[ContinueContextItem])
async def continue_rag_context(
    request: ContinueContextRequest,
) -> list[ContinueContextItem]:
    query = _continue_query(request)
    options = _continue_options(request.options)
    top_k = _continue_top_k(options) if options is not None else None
    fallback_reason: str | None = None
    items: list[ContinueContextItem] = []

    if query is None:
        fallback_reason = "INVALID_QUERY"
    elif options is None:
        fallback_reason = "INVALID_OPTIONS"
    elif top_k is None:
        fallback_reason = "INVALID_TOP_K"
    else:
        try:
            evidence = _retrieve_evidence(query, top_k)
            if evidence is None:
                fallback_reason = "RAG_INVALID_RESPONSE"
            elif not evidence:
                fallback_reason = "NO_EVIDENCE"
            else:
                items = _continue_items(evidence)
        except FileNotFoundError:
            fallback_reason = "RAG_INDEX_NOT_FOUND"
        except ValueError as exc:
            fallback_reason = str(exc) or "RAG_QUERY_FAILED"
        except Exception:
            fallback_reason = "RAG_QUERY_FAILED"

    _log_continue_context(
        input_value=query or "",
        result_count=len(items),
        fallback_reason=fallback_reason,
    )
    return items


def _retrieve_evidence(query: str, top_k: int) -> list[EvidenceItem] | None:
    retrieval = rag_search(query, top_k=top_k)
    if not isinstance(retrieval, dict):
        return None
    return _normalize_evidence(retrieval.get("results", []))


def _normalize_evidence(results: Any) -> list[EvidenceItem]:
    if not isinstance(results, list):
        return []

    evidence: list[EvidenceItem] = []
    for result in results:
        if not isinstance(result, dict):
            continue

        text = str(result.get("snippet") or result.get("text") or "").strip()
        if not text:
            continue

        source = _safe_source(
            result.get("file") or result.get("source") or result.get("doc_id")
        )
        evidence.append(
            EvidenceItem(
                text=text,
                source=source,
                score=_safe_score(result.get("score")),
            )
        )
    return evidence


def _safe_source(value: Any) -> str:
    source = str(value or "unknown").strip() or "unknown"
    path = Path(source)
    if not path.is_absolute():
        return path.as_posix()

    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name or "unknown"


def _safe_score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _continue_query(request: ContinueContextRequest) -> str | None:
    query = _clean_text(request.query)
    if query is not None:
        return query
    return _clean_text(request.fullInput)


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _continue_options(value: Any) -> dict[str, Any] | None:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return None


def _continue_top_k(options: dict[str, Any]) -> int | None:
    raw_value = options.get("top_k", DEFAULT_CONTEXT_TOP_K)
    if isinstance(raw_value, bool) or not isinstance(raw_value, int):
        return None
    if 1 <= raw_value <= 10:
        return raw_value
    return None


def _continue_items(evidence: list[EvidenceItem]) -> list[ContinueContextItem]:
    items: list[ContinueContextItem] = []
    for index, item in enumerate(evidence, start=1):
        items.append(
            ContinueContextItem(
                name=f"nucleo-rag:{index}:{item.source}",
                description=(
                    f"NUCLEO RAG evidence from {item.source}; score={item.score}"
                ),
                content="\n".join(
                    [
                        f"source: {item.source}",
                        f"score: {item.score}",
                        "",
                        item.text,
                    ]
                ),
            )
        )
    return items


def _log_continue_context(
    input_value: str,
    result_count: int,
    fallback_reason: str | None,
) -> None:
    logger.info(
        "continue_rag_context input=%r result_count=%s fallback_reason=%s",
        input_value,
        result_count,
        fallback_reason,
    )


def _error_response(error: str, status_code: int) -> JSONResponse:
    payload = RagQueryResponse(
        status=RagStatus.ERROR,
        evidence=[],
        error=error,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def _validation_error_message(exc: RequestValidationError) -> str:
    messages: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        message = str(error.get("msg", "invalid value"))
        if location:
            messages.append(f"{location}: {message}")
        else:
            messages.append(message)
    return "; ".join(messages) or "invalid request"
