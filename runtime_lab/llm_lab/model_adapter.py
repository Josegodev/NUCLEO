"""Model call adapters for llm_lab experiments.

Adapters are local to runtime_lab/llm_lab and do not call NUCLEO runtime.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Literal

import requests


AdapterMode = Literal["mock_success", "mock_errors", "ollama"]
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_MODEL_ALIASES = {
    "qwen": "qwen2.5-coder:7b",
    "mistral": "mistral",
    "llama3.1:8b": "llama3.1:8b",
}


@dataclass(frozen=True)
class ModelCall:
    model_id: str
    status: str
    output: str | None
    error_type: str | None
    error_message: str | None
    latency_ms: float


def call_model(model_id: str, prompt: str, *, mode: AdapterMode, timeout_ms: int) -> ModelCall:
    start = time.perf_counter()
    try:
        if mode == "mock_success":
            output = _mock_success(model_id, prompt)
        elif mode == "mock_errors":
            output = _mock_errors(model_id, prompt)
        elif mode == "ollama":
            output = _call_ollama_lab_model(model_id, prompt, timeout_ms=timeout_ms)
        else:
            return _error(model_id, "unsupported_feature", f"Unsupported adapter mode: {mode}", start)
    except TimeoutError:
        return _error(model_id, "timeout", "Model call exceeded configured timeout.", start)
    except requests.exceptions.Timeout:
        return _error(model_id, "timeout", "Model call exceeded configured timeout.", start)
    except ModelNotAvailableError:
        return _error(model_id, "model_not_available", "Model is not available in llm_lab.", start)
    except MalformedResponseError:
        return _error(model_id, "malformed_response", "Model returned malformed response.", start)
    except requests.exceptions.ConnectionError:
        return _error(model_id, "model_not_available", "Local model endpoint is not available.", start)
    except requests.exceptions.HTTPError:
        return _error(model_id, "generation_failed", "Local model endpoint returned an HTTP error.", start)
    except requests.exceptions.RequestException:
        return _error(model_id, "generation_failed", "Local model request failed.", start)
    except Exception:
        return _error(model_id, "unknown_error", "Unexpected model adapter error.", start)

    latency_ms = round((time.perf_counter() - start) * 1000, 3)
    if output is None or not output.strip():
        return ModelCall(
            model_id=model_id,
            status="error",
            output=None,
            error_type="malformed_response",
            error_message="Model returned empty output.",
            latency_ms=latency_ms,
        )

    return ModelCall(
        model_id=model_id,
        status="success",
        output=output,
        error_type=None,
        error_message=None,
        latency_ms=latency_ms,
    )


class ModelNotAvailableError(RuntimeError):
    pass


class MalformedResponseError(RuntimeError):
    pass


def _error(model_id: str, error_type: str, message: str, start: float) -> ModelCall:
    return ModelCall(
        model_id=model_id,
        status="error",
        output=None,
        error_type=error_type,
        error_message=message or "Unknown model call error.",
        latency_ms=round((time.perf_counter() - start) * 1000, 3),
    )


def _mock_success(model_id: str, prompt: str) -> str:
    if "FINAL RANKING" in prompt:
        labels = _labels_from_prompt(prompt)
        ordered = list(reversed(labels))
        ranking = "\n".join(f"{index}. {label}" for index, label in enumerate(ordered, start=1))
        return f"{model_id} review: responses were evaluated deterministically.\n\nFINAL RANKING:\n{ranking}"
    if "SYNTHESIZE_FINAL" in prompt:
        return f"{model_id} synthesis: deterministic final answer from stored stage artifacts."
    return f"{model_id} response: deterministic answer for prompt length {len(prompt)}."


def _mock_errors(model_id: str, prompt: str) -> str:
    if model_id.endswith("unavailable"):
        raise ModelNotAvailableError("Mock model is unavailable.")
    if model_id.endswith("empty"):
        return ""
    if "FINAL RANKING" in prompt and model_id.endswith("bad-ranking"):
        return "This review intentionally omits the required complete ranking."
    if "SYNTHESIZE_FINAL" in prompt and model_id.endswith("chairman-empty"):
        return ""
    return _mock_success(model_id, prompt)


def _labels_from_prompt(prompt: str) -> list[str]:
    import re

    labels = []
    for label in re.findall(r"Response [A-Z]", prompt):
        if label not in labels:
            labels.append(label)
    return labels


def _call_ollama_lab_model(model_id: str, prompt: str, *, timeout_ms: int) -> str:
    """Call local Ollama through one deterministic llm_lab adapter path."""
    ollama_model = _resolve_ollama_model(model_id)
    messages = [
        {
            "role": "system",
            "content": (
                "You are running inside runtime_lab/llm_lab. "
                "Answer only the current experiment prompt. "
                "Do not assume access to NUCLEO Runtime, tools, or policy."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    timeout_seconds = max(timeout_ms / 1000, 1)
    _ensure_ollama_model_available(ollama_model, timeout_seconds=timeout_seconds)
    response = requests.post(
        OLLAMA_URL,
        json={"model": ollama_model, "messages": messages, "stream": False},
        timeout=timeout_seconds,
    )
    if response.status_code == 404:
        raise ModelNotAvailableError("Ollama model was not found.")
    response.raise_for_status()
    return _extract_ollama_answer(response)


def _resolve_ollama_model(model_id: str) -> str:
    try:
        return OLLAMA_MODEL_ALIASES[model_id]
    except KeyError as exc:
        raise ModelNotAvailableError(f"Unsupported llm_lab Ollama model: {model_id}") from exc


def _ensure_ollama_model_available(ollama_model: str, *, timeout_seconds: float) -> None:
    response = requests.get(OLLAMA_TAGS_URL, timeout=timeout_seconds)
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as exc:
        raise MalformedResponseError("Ollama model list response was not valid JSON.") from exc

    models = payload.get("models")
    if not isinstance(models, list):
        raise MalformedResponseError("Ollama model list response did not contain a models list.")

    available = {
        item.get("name")
        for item in models
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if ollama_model not in available:
        raise ModelNotAvailableError(f"Ollama model is not installed: {ollama_model}")


def _extract_ollama_answer(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError as exc:
        raise MalformedResponseError("Ollama response was not valid JSON.") from exc

    message = payload.get("message")
    if not isinstance(message, dict):
        raise MalformedResponseError("Ollama response did not contain a message object.")

    content = message.get("content")
    if not isinstance(content, str):
        raise MalformedResponseError("Ollama response message did not contain string content.")

    return content.strip()
