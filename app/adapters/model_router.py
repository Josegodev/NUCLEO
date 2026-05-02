"""Model routing boundary for controlled Planner augmentation.

The runtime talks to this adapter, not directly to llm_lab providers. The
adapter normalizes local Ollama and OpenAI responses into one small contract.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass

import requests

from app.schemas.artifacts import JsonValue
from app.schemas.requests import (
    ALLOWED_AUGMENTATION_MODELS,
    DEFAULT_AUGMENTATION_MODEL_ID,
    AgentBackend,
    resolve_augmentation_model_id,
)
from runtime_lab.llm_lab.model_adapter import call_model


DEFAULT_LOCAL_MODEL_ID = DEFAULT_AUGMENTATION_MODEL_ID
DEFAULT_OPENAI_MODEL_ID = "gpt-4o-mini"
DEFAULT_TIMEOUT_MS = 120000
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_FALLBACK_MODEL_ENV = "NUCLEO_OPENAI_FALLBACK_MODEL"
ALLOWED_MODELS = ALLOWED_AUGMENTATION_MODELS
ALLOWED_OPENAI_MODELS = {DEFAULT_OPENAI_MODEL_ID}
LOCAL_MODEL_IDS = ALLOWED_MODELS


@dataclass(frozen=True)
class ModelBackendCall:
    backend_used: AgentBackend
    model_used: str
    success: bool
    output: str | None
    latency_ms: float
    error_type: str | None = None
    error_message: str | None = None


BackendCaller = Callable[[str, str], ModelBackendCall]


class ModelRouter:
    def __init__(
        self,
        local_caller: BackendCaller | None = None,
        openai_caller: BackendCaller | None = None,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
    ) -> None:
        self._local_caller = local_caller or self._call_local
        self._openai_caller = openai_caller or self._call_openai
        self._timeout_ms = timeout_ms

    def generate(
        self,
        prompt: str,
        backend: AgentBackend | str,
        model_id: str | None,
    ) -> dict[str, JsonValue]:
        selected_backend = AgentBackend(backend)
        selected_model, model_resolution_reason = self._resolve_model_id(
            model_id,
            selected_backend,
        )
        start = time.perf_counter()

        if selected_backend == AgentBackend.LOCAL:
            result = self._local_caller(selected_model, prompt)
            return self._to_router_result(
                result,
                start=start,
                fallback_used=model_resolution_reason is not None,
                fallback_reason=model_resolution_reason,
                model_resolution_reason=model_resolution_reason,
            )

        if selected_backend == AgentBackend.OPENAI:
            result = self._openai_caller(selected_model, prompt)
            return self._to_router_result(
                result,
                start=start,
                fallback_used=model_resolution_reason is not None,
                fallback_reason=model_resolution_reason,
                model_resolution_reason=model_resolution_reason,
            )

        local_result = self._local_caller(selected_model, prompt)
        if local_result.success:
            return self._to_router_result(
                local_result,
                start=start,
                fallback_used=model_resolution_reason is not None,
                fallback_reason=model_resolution_reason,
                model_resolution_reason=model_resolution_reason,
            )

        fallback_reason = self._combine_reasons(
            model_resolution_reason,
            self._failure_reason(local_result),
        )
        openai_model = self._openai_fallback_model(selected_model)
        openai_result = self._openai_caller(openai_model, prompt)
        if openai_result.success:
            return self._to_router_result(
                openai_result,
                start=start,
                fallback_used=True,
                fallback_reason=fallback_reason,
                model_resolution_reason=model_resolution_reason,
            )

        return self._to_router_result(
            openai_result,
            start=start,
            fallback_used=True,
            fallback_reason=self._combine_reasons(
                fallback_reason,
                self._failure_reason(openai_result),
            ),
            model_resolution_reason=model_resolution_reason,
        )

    def _call_local(self, model_id: str, prompt: str) -> ModelBackendCall:
        call = call_model(
            model_id,
            prompt,
            mode="ollama",
            timeout_ms=self._timeout_ms,
        )
        return ModelBackendCall(
            backend_used=AgentBackend.LOCAL,
            model_used=call.model_id,
            success=call.status == "success",
            output=call.output,
            latency_ms=call.latency_ms,
            error_type=call.error_type,
            error_message=call.error_message,
        )

    def _call_openai(self, model_id: str, prompt: str) -> ModelBackendCall:
        start = time.perf_counter()
        api_key = os.getenv(OPENAI_API_KEY_ENV)
        openai_model = self._openai_fallback_model(model_id)
        if not api_key:
            return self._failed_openai_call(
                openai_model,
                start,
                "model_not_available",
                f"{OPENAI_API_KEY_ENV} is not configured.",
            )

        timeout_seconds = max(self._timeout_ms / 1000, 1)
        try:
            response = requests.post(
                OPENAI_CHAT_COMPLETIONS_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                },
                timeout=timeout_seconds,
            )
            response.raise_for_status()
            output = self._extract_openai_output(response)
        except requests.exceptions.Timeout:
            return self._failed_openai_call(
                openai_model,
                start,
                "timeout",
                "OpenAI model call exceeded configured timeout.",
            )
        except requests.exceptions.RequestException:
            return self._failed_openai_call(
                openai_model,
                start,
                "generation_failed",
                "OpenAI model request failed.",
            )
        except ValueError:
            return self._failed_openai_call(
                openai_model,
                start,
                "malformed_response",
                "OpenAI model returned malformed response.",
            )

        if not output.strip():
            return self._failed_openai_call(
                openai_model,
                start,
                "malformed_response",
                "OpenAI model returned empty output.",
            )

        return ModelBackendCall(
            backend_used=AgentBackend.OPENAI,
            model_used=openai_model,
            success=True,
            output=output.strip(),
            latency_ms=self._elapsed_ms(start),
        )

    @staticmethod
    def _extract_openai_output(response: requests.Response) -> str:
        payload = response.json()
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("OpenAI response did not contain choices.")

        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise ValueError("OpenAI choice did not contain message.")

        content = message.get("content")
        if not isinstance(content, str):
            raise ValueError("OpenAI message did not contain string content.")

        return content

    def _failed_openai_call(
        self,
        model_id: str,
        start: float,
        error_type: str,
        error_message: str,
    ) -> ModelBackendCall:
        return ModelBackendCall(
            backend_used=AgentBackend.OPENAI,
            model_used=model_id,
            success=False,
            output=None,
            latency_ms=self._elapsed_ms(start),
            error_type=error_type,
            error_message=error_message,
        )

    @staticmethod
    def _openai_fallback_model(model_id: str) -> str:
        configured = os.getenv(OPENAI_FALLBACK_MODEL_ENV)
        if configured:
            return configured.strip()

        if model_id in LOCAL_MODEL_IDS:
            return DEFAULT_OPENAI_MODEL_ID

        return model_id or DEFAULT_OPENAI_MODEL_ID

    @staticmethod
    def _to_router_result(
        result: ModelBackendCall,
        *,
        start: float,
        fallback_used: bool = False,
        fallback_reason: str | None = None,
        model_resolution_reason: str | None = None,
    ) -> dict[str, JsonValue]:
        return {
            "output": result.output or "",
            "model_used": result.model_used,
            "backend_used": result.backend_used.value,
            "latency_ms": round((time.perf_counter() - start) * 1000, 3),
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason or result.error_message,
            "model_resolution_reason": model_resolution_reason,
        }

    @staticmethod
    def _failure_reason(result: ModelBackendCall) -> str:
        reason = result.error_message or "model call failed"
        if result.error_type:
            return f"{result.backend_used.value}:{result.error_type}: {reason}"
        return f"{result.backend_used.value}: {reason}"

    @staticmethod
    def _elapsed_ms(start: float) -> float:
        return round((time.perf_counter() - start) * 1000, 3)

    @staticmethod
    def _resolve_model_id(
        model_id: str | None,
        backend: AgentBackend,
    ) -> tuple[str, str | None]:
        requested_model = (model_id or "").strip()
        if backend == AgentBackend.OPENAI and requested_model in ALLOWED_OPENAI_MODELS:
            return requested_model, None

        return resolve_augmentation_model_id(model_id)

    @staticmethod
    def _combine_reasons(*reasons: str | None) -> str | None:
        filtered_reasons = [reason for reason in reasons if reason]
        if not filtered_reasons:
            return None
        return "; ".join(filtered_reasons)
