"""FastAPI lab server for llm_lab experiment artifacts.

This server is deliberately outside NUCLEO core. It only reads/writes
runtime_lab/llm_lab artifacts and invokes the local llm_lab experiment runner.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator


REPO_ROOT = Path(__file__).resolve().parents[3]
LLM_LAB_DIR = REPO_ROOT / "runtime_lab" / "llm_lab"
ARTIFACTS_DIR = LLM_LAB_DIR / "artifacts"
FRONTEND_DIR = REPO_ROOT / "runtime_lab" / "llm_lab_ui" / "frontend"

if str(LLM_LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LLM_LAB_DIR))

from experiment_runner import default_config, run_experiment  # noqa: E402
from experiment_validator import ArtifactValidationError, validate_artifact  # noqa: E402
from llm_rag_answer import NO_EVIDENCE_FOR_ANSWER, build_grounded_rag_prompt  # noqa: E402
from model_adapter import OLLAMA_MODEL_ALIASES  # noqa: E402
from rag_nucleo_docs.rag_answer import build_answer  # noqa: E402
from rag_nucleo_docs.lmstudio_adapter import call_lmstudio_model  # noqa: E402
from rag_nucleo_docs.search import search as rag_search  # noqa: E402


ALLOWED_MODES = {"mock", "mock-success", "ollama"}
ALLOWED_LOCAL_MODELS = set(OLLAMA_MODEL_ALIASES)
ALLOWED_RAG_MODELS = {"llama3.1:8b", "mistral", "qwen"}
EXTERNAL_RAG_MODELS = {"external/openai", "external/anthropic", "external/custom"}
DEFAULT_LOCAL_MODELS = ["qwen", "mistral", "llama3.1:8b"]
MOCK_SUCCESS_MODELS = ["mock/model-a", "mock/model-b", "mock/model-c"]
MOCK_ERROR_STAGE1 = ["mock/model-a", "mock/model-unavailable", "mock/model-empty"]
MOCK_ERROR_REVIEWERS = ["mock/model-a", "mock/model-bad-ranking"]
RAG_MODEL_ANSWER_TIMEOUT_MS = 120000
RAG_MODEL_ANSWER_WARNING = (
    "Experimental model answer grounded on retrieved evidence. "
    "Not part of NUCLEO runtime."
)


app = FastAPI(title="NUCLEO llm_lab UI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ExperimentRequest(BaseModel):
    mode: Literal["mock", "mock-success", "ollama"]
    input: str = Field(min_length=1)
    stage1_models: list[str] = Field(default_factory=lambda: list(DEFAULT_LOCAL_MODELS))
    stage2_reviewers: list[str] = Field(default_factory=lambda: list(DEFAULT_LOCAL_MODELS))
    chairman: str = "qwen"

    @field_validator("input")
    @classmethod
    def input_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("input must not be blank")
        return value

    @field_validator("stage1_models", "stage2_reviewers")
    @classmethod
    def model_lists_must_be_known(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("model list must not be empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("model list must not contain duplicates")
        unknown = sorted(set(cleaned) - ALLOWED_LOCAL_MODELS)
        if unknown:
            raise ValueError(f"unsupported local model(s): {', '.join(unknown)}")
        return cleaned

    @field_validator("chairman")
    @classmethod
    def chairman_must_be_known(cls, value: str) -> str:
        value = value.strip()
        if value not in ALLOWED_LOCAL_MODELS:
            allowed = ", ".join(sorted(ALLOWED_LOCAL_MODELS))
            raise ValueError(f"chairman must be one of: {allowed}")
        return value


class RagRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    model: str | None = None

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value


class RagModelAnswerRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    model: str | None = None

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "llm_lab_ui",
        "scope": "runtime_lab_only",
    }


@app.get("/api/artifacts")
async def list_artifacts() -> list[dict[str, object]]:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, object]] = []
    for path in sorted(ARTIFACTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if path.name.endswith(".tmp.json"):
            continue
        try:
            artifact = _read_artifact_file(path)
            items.append(
                {
                    "experiment_id": artifact["experiment_id"],
                    "created_at": artifact["created_at"],
                    "completed_at": artifact.get("completed_at"),
                    "status": artifact["status"],
                    "artifact_path": str(path.relative_to(REPO_ROOT)),
                    "mode": artifact.get("config", {}).get("backend_profile"),
                    "input_preview": artifact.get("input", {}).get("user_input", "")[:120],
                    "contract_valid": True,
                }
            )
        except HTTPException as exc:
            items.append(_invalid_artifact_metadata(path, str(exc.detail)))
    return items


@app.get("/api/artifacts/{experiment_id}")
async def get_artifact(experiment_id: str) -> dict[str, object]:
    _validate_experiment_id(experiment_id)
    path = ARTIFACTS_DIR / f"{experiment_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return _read_artifact_file(path)


@app.post("/api/experiments")
async def create_experiment(request: ExperimentRequest) -> dict[str, str]:
    mode = request.mode
    if mode not in ALLOWED_MODES:
        raise HTTPException(status_code=400, detail="Unsupported mode")

    try:
        if mode == "mock-success":
            artifact_path = run_experiment(
                user_input=request.input,
                stage1_responders=MOCK_SUCCESS_MODELS,
                stage2_reviewers=MOCK_SUCCESS_MODELS,
                stage3_chairman="mock/chairman",
                adapter_mode="mock_success",
                config=default_config("mock_success", 120000),
                notes="llm_lab_ui mock-success experiment.",
            )
        elif mode == "mock":
            artifact_path = run_experiment(
                user_input=request.input,
                stage1_responders=MOCK_ERROR_STAGE1,
                stage2_reviewers=MOCK_ERROR_REVIEWERS,
                stage3_chairman="mock/chairman-empty",
                adapter_mode="mock_errors",
                config=default_config("mock_errors", 120000),
                notes="llm_lab_ui mock experiment with explicit errors.",
            )
        else:
            artifact_path = run_experiment(
                user_input=request.input,
                stage1_responders=request.stage1_models,
                stage2_reviewers=request.stage2_reviewers,
                stage3_chairman=request.chairman,
                adapter_mode="ollama",
                config=default_config("ollama", 120000),
                notes="llm_lab_ui local Ollama experiment.",
            )
    except ArtifactValidationError as exc:
        raise HTTPException(status_code=500, detail=f"Artifact validation failed: {exc}") from exc

    artifact = _read_artifact_file(artifact_path)
    return {
        "experiment_id": artifact["experiment_id"],
        "artifact_path": str(artifact_path.relative_to(REPO_ROOT)),
        "status": artifact["status"],
    }


@app.post("/rag/search")
async def search_rag(request: RagRequest) -> dict[str, object]:
    try:
        _validate_rag_model(request.model)
        return rag_search(request.query, top_k=request.top_k)
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="RAG_INDEX_NOT_FOUND") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="INTERNAL_ERROR") from exc


@app.post("/rag/answer")
async def answer_rag(request: RagRequest) -> dict[str, object]:
    try:
        _validate_rag_model(request.model)
        return build_answer(request.query, top_k=request.top_k)
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="RAG_INDEX_NOT_FOUND") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="INTERNAL_ERROR") from exc


@app.post("/rag/model-answer")
async def answer_rag_with_model(request: RagModelAnswerRequest) -> dict[str, object]:
    try:
        model = _validate_rag_model(request.model, required=True)
        retrieval = rag_search(request.query, top_k=request.top_k)
        evidence = _normalize_model_answer_evidence(retrieval)
        if not evidence:
            return {
                "status": "NO_EVIDENCE",
                "query": request.query,
                "model": model,
                "answer": NO_EVIDENCE_FOR_ANSWER,
                "evidence": [],
                "fallback_used": False,
                "fallback_reason": None,
                "warning": RAG_MODEL_ANSWER_WARNING,
            }

        prompt = build_grounded_rag_prompt(request.query, evidence)
        result = call_lmstudio_model(
            model,
            prompt,
            timeout_ms=RAG_MODEL_ANSWER_TIMEOUT_MS,
        )
        if result.status != "success":
            return {
                "status": "MODEL_ERROR",
                "query": request.query,
                "model": model,
                "answer": "",
                "evidence": evidence,
                "fallback_used": True,
                "fallback_reason": _summarize_model_error(result),
                "warning": RAG_MODEL_ANSWER_WARNING,
            }

        return {
            "status": "MODEL_ANSWER_READY",
            "query": request.query,
            "model": model,
            "answer": result.output or "",
            "evidence": evidence,
            "fallback_used": False,
            "fallback_reason": None,
            "warning": RAG_MODEL_ANSWER_WARNING,
        }
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="RAG_INDEX_NOT_FOUND") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="INTERNAL_ERROR") from exc


def _read_artifact_file(path: Path) -> dict[str, object]:
    try:
        resolved = path.resolve()
        artifacts_root = ARTIFACTS_DIR.resolve()
        if artifacts_root not in resolved.parents:
            raise HTTPException(status_code=400, detail="Invalid artifact path")
        artifact = json.loads(resolved.read_text(encoding="utf-8"))
        validate_artifact(artifact)
        return artifact
    except HTTPException:
        raise
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid artifact JSON: {path.name}") from exc
    except ArtifactValidationError as exc:
        raise HTTPException(status_code=500, detail=f"Artifact contract violation: {path.name}: {exc}") from exc


def _validate_rag_model(model: str | None, *, required: bool = False) -> str | None:
    if model is None or not model.strip():
        if required:
            raise ValueError("model is required")
        return None
    model = model.strip()
    if model in EXTERNAL_RAG_MODELS or model.startswith("external/"):
        raise HTTPException(status_code=400, detail="EXTERNAL_MODEL_NOT_ENABLED")
    if model not in ALLOWED_RAG_MODELS:
        allowed = ", ".join(sorted(ALLOWED_RAG_MODELS))
        raise ValueError(f"Unsupported RAG model: {model}. Allowed models: {allowed}")
    return model


def _normalize_model_answer_evidence(retrieval: object) -> list[dict[str, object]]:
    if not isinstance(retrieval, Mapping):
        return []

    raw_results = retrieval.get("results", [])
    if not isinstance(raw_results, list):
        return []

    evidence: list[dict[str, object]] = []
    for result in raw_results:
        result_map = _object_to_mapping(result)
        if result_map is None:
            continue
        snippet = str(result_map.get("snippet") or result_map.get("text") or "").strip()
        if not snippet:
            continue
        doc_id = result_map.get("doc_id") or result_map.get("chunk_id")
        source = result_map.get("source") or result_map.get("file") or doc_id
        evidence.append(
            {
                "doc_id": doc_id,
                "chunk_id": result_map.get("chunk_id") or doc_id,
                "source": source,
                "score": result_map.get("score"),
                "heading": result_map.get("heading"),
                "start_line": result_map.get("start_line"),
                "end_line": result_map.get("end_line"),
                "snippet": snippet,
            }
        )
    return evidence


def _object_to_mapping(value: object) -> dict[str, object] | None:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return dict(dumped) if isinstance(dumped, Mapping) else None
    return None


def _summarize_model_error(result: object) -> str:
    error_type = getattr(result, "error_type", None)
    error_message = getattr(result, "error_message", None)
    if error_type and error_message:
        return f"{error_type}: {error_message}"
    if error_message:
        return str(error_message)
    return "LM Studio model call failed"


def _validate_experiment_id(experiment_id: str) -> None:
    import uuid

    try:
        uuid.UUID(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid experiment_id") from exc


def _invalid_artifact_metadata(path: Path, reason: str) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        raw = {}
    experiment_id = raw.get("experiment_id", path.stem)
    return {
        "experiment_id": experiment_id,
        "created_at": raw.get("created_at"),
        "completed_at": raw.get("completed_at"),
        "status": "contract_error",
        "artifact_path": str(path.relative_to(REPO_ROOT)),
        "mode": raw.get("config", {}).get("backend_profile") if isinstance(raw.get("config"), dict) else None,
        "input_preview": raw.get("input", {}).get("user_input", "")[:120] if isinstance(raw.get("input"), dict) else "",
        "contract_valid": False,
        "contract_error": reason,
    }
