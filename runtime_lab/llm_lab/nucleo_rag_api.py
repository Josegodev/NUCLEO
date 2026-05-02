"""HTTP API for deterministic NUCLEO documentation retrieval.

This module belongs to runtime_lab/llm_lab only. It exposes existing
rag_nucleo_docs retrieval as read-only evidence and does not call LLMs,
NUCLEO runtime components, policies, registries, or tools.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from runtime_lab.llm_lab.rag_nucleo_docs.search import search as rag_search


REPO_ROOT = Path(__file__).resolve().parents[2]


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
