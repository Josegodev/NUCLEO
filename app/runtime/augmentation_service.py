"""Controlled LLM augmentation boundary.

This service may ask a model for a proposal, but it cannot authorize, resolve,
or execute tools. It receives a serialized tool catalog instead of a live
ToolRegistry instance.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationError

from app.adapters.model_router import ModelRouter
from app.domain.tool_proposals.models import AgentActionProposal
from app.schemas.artifacts import JsonValue, ToolContractArtifact, validate_tool_payload
from app.schemas.context import ExecutionContext
from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentRequest


class ToolContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    input_schema: dict[str, JsonValue] = Field(default_factory=dict)


class AugmentationProposedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(min_length=1)
    arguments: dict[str, JsonValue] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


class AugmentationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["augmentation_result.v1"] = "augmentation_result.v1"
    mode: Literal["proposal"] = "proposal"
    assistant_message: str = Field(min_length=1)
    proposed_action: AugmentationProposedAction | None = None
    fallback_used: bool
    fallback_reason: str | None = None
    validation_errors: list[str] = Field(default_factory=list)

    _raw_output: str | None = PrivateAttr(default=None)
    _model_router: dict[str, JsonValue] | None = PrivateAttr(default=None)

    @property
    def raw_output(self) -> str | None:
        return self._raw_output

    @property
    def model_router(self) -> dict[str, JsonValue] | None:
        return self._model_router

    def with_runtime_metadata(
        self,
        *,
        raw_output: str | None,
        model_router: dict[str, JsonValue] | None,
    ) -> "AugmentationResult":
        self._raw_output = raw_output
        self._model_router = model_router
        return self


class LLMPlannerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str
    context: list[str]
    constraints: list[str]


class LLMAugmentationTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm_input: LLMPlannerInput
    raw_output: str | None = None
    validated_output: dict[str, JsonValue] | None = None
    model_router: dict[str, JsonValue] | None = None
    accepted: bool
    reason: str = Field(min_length=1)
    fallback_reason: str | None = None


LLMProviderResult = str | dict[str, JsonValue]
LLMProposalProvider = Callable[[LLMPlannerInput, AgentRequest], LLMProviderResult]


def serialize_tool_catalog(tool_registry) -> list[ToolContract]:
    return [
        ToolContract(name=contract.name, input_schema=contract.input_schema)
        for contract in tool_registry.list_contracts()
        if isinstance(contract, ToolContractArtifact)
    ]


def _strip_json_fence(raw: str) -> str:
    normalized = raw.strip()
    if not normalized.startswith("```"):
        return normalized

    lines = normalized.splitlines()
    if len(lines) < 2:
        raise ValueError("Invalid fenced JSON block from LLM output")

    first_line = lines[0].strip()
    if first_line not in {"```", "```json"}:
        raise ValueError("Invalid fenced JSON block language from LLM output")

    if lines[-1].strip() != "```":
        raise ValueError("Invalid fenced JSON block closing marker from LLM output")

    return "\n".join(lines[1:-1]).strip()


def build_tool_catalog_prompt(tool_catalog: list[ToolContract]) -> str:
    lines = [
        "Available tools and required argument schemas:",
        "",
    ]

    for contract in sorted(tool_catalog, key=lambda item: item.name):
        lines.append(f"- {contract.name}")
        lines.append("  arguments:")
        properties = contract.input_schema.get("properties", {})
        required = set(contract.input_schema.get("required", []))
        if not properties:
            lines.append("    {}")
            lines.append("")
            continue

        for field_name in sorted(properties):
            field_schema = properties[field_name]
            type_label = _schema_type_label(field_schema)
            optional_label = "" if field_name in required else " (optional)"
            lines.append(f"    {field_name}: {type_label}{optional_label}")
        lines.append("")

    lines.extend(
        [
            "Rules:",
            "- Use ONLY listed tools.",
            "- Use EXACT argument names.",
            "- Do NOT invent fields.",
            "- Do NOT use aliases.",
            "- If no tool fits, return suggested_action=null and arguments={}.",
            "- Output ONLY JSON, optionally fenced as ```json ... ```.",
        ]
    )
    return "\n".join(lines)


def _schema_type_label(schema: object) -> str:
    if not isinstance(schema, dict):
        return "unknown"

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        return " | ".join(_schema_type_label(item) for item in any_of)

    schema_type = schema.get("type")
    if isinstance(schema_type, str):
        return schema_type

    return "unknown"


def build_llm_input(request: AgentRequest) -> LLMPlannerInput:
    context: list[str] = []
    if request.tool:
        context.append(f"explicit_tool={request.tool}")
    if request.payload:
        context.append(
            "payload_keys=" + ",".join(sorted(str(key) for key in request.payload))
        )
    if request.options:
        context.append(f"backend={request.options.backend.value}")
        context.append(f"model_id={request.options.model_id}")
        context.append(f"agent_mode={request.options.agent_mode.value}")
    if request.augmentation and request.augmentation.model_id:
        context.append(f"augmentation_model_id={request.augmentation.model_id}")

    return LLMPlannerInput(
        goal=request.user_input or "",
        context=context,
        constraints=[
            "Return valid JSON only.",
            "Use fields: intent, suggested_action, arguments, confidence.",
            "Propose tools only; never execute tools.",
            "Use serialized catalog tools only.",
            "PolicyEngine remains the final authority before execution.",
            "ToolRegistry must not be modified.",
            "dry_run remains true for Productive Agent Console v0.",
        ],
    )


def validate_llm_proposal(
    raw_output: str,
    tool_catalog: list[ToolContract],
) -> AgentActionProposal:
    try:
        decoded_output = json.loads(_strip_json_fence(raw_output))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid JSON from LLM output") from exc

    proposal = _validate_llm_shape(decoded_output)
    if proposal.suggested_action is None:
        return proposal

    catalog_names = {contract.name for contract in tool_catalog}
    if proposal.suggested_action not in catalog_names:
        raise ValueError(
            f"LLM referenced tool outside serialized catalog: "
            f"{proposal.suggested_action}"
        )

    try:
        validated_payload = validate_tool_payload(
            proposal.suggested_action,
            proposal.arguments,
        )
    except (TypeError, ValueError, ValidationError) as exc:
        raise ValueError(
            f"LLM payload does not match tool contract for "
            f"'{proposal.suggested_action}': {exc}"
        ) from exc

    return AgentActionProposal(
        intent=proposal.intent,
        suggested_action=proposal.suggested_action,
        arguments=validated_payload,
        confidence=proposal.confidence,
    )


def _validate_llm_shape(decoded_output: object) -> AgentActionProposal:
    if not isinstance(decoded_output, dict):
        raise ValueError("LLM output must be a JSON object")

    expected_fields = {"intent", "suggested_action", "arguments", "confidence"}
    unexpected_fields = sorted(set(decoded_output) - expected_fields)
    if unexpected_fields:
        raise ValueError(
            "LLM output contains unexpected fields: " + ", ".join(unexpected_fields)
        )

    intent = _required_string(decoded_output, "intent")
    suggested_action_value = decoded_output.get("suggested_action")
    if suggested_action_value is None:
        suggested_action = None
    else:
        suggested_action = _required_string(decoded_output, "suggested_action")

    arguments = decoded_output.get("arguments")
    if not isinstance(arguments, dict):
        raise ValueError("LLM output field 'arguments' must be an object")
    if suggested_action is None and arguments:
        raise ValueError("LLM output with suggested_action=null must use empty arguments")

    confidence = decoded_output.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, int | float):
        raise ValueError("LLM output field 'confidence' must be a number")
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError("LLM output field 'confidence' must be between 0 and 1")

    return AgentActionProposal(
        intent=intent,
        suggested_action=suggested_action,
        arguments=arguments,
        confidence=float(confidence),
    )


def _required_string(payload: dict, field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"LLM output field '{field_name}' must be a string")
    return value.strip()


def augmentation_result_from_proposal(
    proposal: AgentActionProposal,
) -> AugmentationResult:
    proposed_action = None
    if proposal.suggested_action is not None:
        proposed_action = AugmentationProposedAction(
            tool_name=proposal.suggested_action,
            arguments=proposal.arguments,
            confidence=proposal.confidence,
        )

    return AugmentationResult(
        mode="proposal",
        assistant_message=proposal.intent,
        proposed_action=proposed_action,
        fallback_used=False,
        fallback_reason=None,
        validation_errors=[],
    )


def fallback_augmentation_result(
    reason: str,
    *,
    raw_output: str | None = None,
    model_router: dict[str, JsonValue] | None = None,
) -> AugmentationResult:
    return AugmentationResult(
        mode="proposal",
        assistant_message="Deterministic fallback used.",
        proposed_action=None,
        fallback_used=True,
        fallback_reason=reason,
        validation_errors=[reason],
    ).with_runtime_metadata(raw_output=raw_output, model_router=model_router)


def build_augmentation_metadata(
    result: AugmentationResult,
    request: AgentRequest | None = None,
    fallback_plan: PlannedAction | None = None,
) -> dict[str, JsonValue]:
    if fallback_plan is not None:
        proposal = _proposal_from_plan(fallback_plan)
    else:
        proposal = _proposal_from_result(result)

    metadata: dict[str, JsonValue] = {
        "augmentation_attempted": True,
        "proposal": proposal,
        "model_output": result.raw_output or "",
        "fallback_used": result.fallback_used,
        "fallback_reason": result.fallback_reason,
        "validation_errors": list(result.validation_errors),
    }

    request_model_resolution_reason = (
        request.model_resolution_reason if request is not None else None
    )

    if request and request.options:
        metadata["backend"] = request.options.backend.value
        metadata["model_id"] = request.options.model_id

    router_result = result.model_router
    if router_result:
        for key in (
            "model_used",
            "backend_used",
            "latency_ms",
            "fallback_used",
            "fallback_reason",
            "model_resolution_reason",
        ):
            if key in router_result:
                metadata[key] = router_result[key]
        if result.fallback_used:
            metadata["fallback_used"] = True
            router_reason = router_result.get("fallback_reason")
            if isinstance(router_reason, str) and router_reason:
                metadata["fallback_reason"] = f"{router_reason}; {result.fallback_reason}"
            else:
                metadata["fallback_reason"] = result.fallback_reason

    if request_model_resolution_reason:
        existing_reason = metadata.get("fallback_reason")
        metadata["model_resolution_reason"] = request_model_resolution_reason
        metadata["fallback_used"] = True
        if isinstance(existing_reason, str) and existing_reason:
            metadata["fallback_reason"] = (
                f"{request_model_resolution_reason}; {existing_reason}"
            )
        else:
            metadata["fallback_reason"] = request_model_resolution_reason

    return metadata


def _proposal_from_result(result: AugmentationResult) -> dict[str, JsonValue]:
    if result.proposed_action is None:
        return {
            "intent": result.assistant_message,
            "suggested_action": None,
            "arguments": {},
            "confidence": 0.0,
        }

    return {
        "intent": result.assistant_message,
        "suggested_action": result.proposed_action.tool_name,
        "arguments": result.proposed_action.arguments,
        "confidence": result.proposed_action.confidence,
    }


def _proposal_from_plan(plan: PlannedAction) -> dict[str, JsonValue]:
    return {
        "intent": plan.reason,
        "suggested_action": plan.tool_name or "no_plan",
        "arguments": plan.payload,
        "confidence": plan.confidence,
    }


class ModelRouterProposalProvider:
    def __init__(
        self,
        model_router: ModelRouter | None = None,
        tool_catalog: list[ToolContract] | None = None,
        tool_registry=None,
    ) -> None:
        self._model_router = model_router or ModelRouter()
        if tool_catalog is not None:
            self._tool_catalog = list(tool_catalog)
        elif tool_registry is not None:
            self._tool_catalog = serialize_tool_catalog(tool_registry)
        else:
            self._tool_catalog = []

    def __call__(
        self,
        llm_input: LLMPlannerInput,
        request: AgentRequest,
    ) -> dict[str, JsonValue]:
        options = request.options
        backend = options.backend if options else "auto"
        model_id = AugmentationService._requested_model_id(request)
        return self._model_router.generate(
            prompt=self._build_prompt(llm_input),
            backend=backend,
            model_id=model_id,
        )

    def _build_prompt(self, llm_input: LLMPlannerInput) -> str:
        return build_model_prompt(llm_input, self._tool_catalog)


def build_model_prompt(
    llm_input: LLMPlannerInput,
    tool_catalog: list[ToolContract],
) -> str:
    return "\n".join(
        [
            "You are augmenting the NUCLEO Planner.",
            "Return JSON only, with exactly these fields:",
            '{"intent": string, "suggested_action": string | null, "arguments": object, "confidence": number}',
            build_tool_catalog_prompt(tool_catalog),
            "Do not execute tools.",
            "Do not authorize actions.",
            "The PolicyEngine and ToolRegistry will validate the proposal.",
            f"Goal: {llm_input.goal}",
            f"Context: {json.dumps(llm_input.context, ensure_ascii=True)}",
            f"Constraints: {json.dumps(llm_input.constraints, ensure_ascii=True)}",
        ]
    )


class AugmentationService:
    def __init__(
        self,
        proposal_provider: LLMProposalProvider | None = None,
        model_router: ModelRouter | None = None,
    ) -> None:
        self._proposal_provider = proposal_provider
        self._model_router = model_router or ModelRouter()
        self._audit_records: list[LLMAugmentationTrace] = []

    @property
    def audit_records(self) -> list[LLMAugmentationTrace]:
        return list(self._audit_records)

    def run(
        self,
        request: AgentRequest,
        context: ExecutionContext | None,
        tool_catalog: list[ToolContract],
    ) -> AugmentationResult:
        llm_input = build_llm_input(request)
        raw_output: str | None = None
        router_result: dict[str, JsonValue] | None = None

        try:
            provider_result = self._call_provider(llm_input, request, tool_catalog)
            raw_output, router_result = self._normalize_provider_result(provider_result)
            proposal = validate_llm_proposal(raw_output, tool_catalog)
            result = augmentation_result_from_proposal(proposal).with_runtime_metadata(
                raw_output=raw_output,
                model_router=router_result,
            )
        except Exception as exc:
            reason = f"LLM proposal rejected; deterministic fallback used: {exc}"
            result = fallback_augmentation_result(
                reason,
                raw_output=raw_output,
                model_router=router_result,
            )
            self._record_trace(
                llm_input=llm_input,
                result=result,
                accepted=False,
                reason=reason,
            )
            return result

        self._record_trace(
            llm_input=llm_input,
            result=result,
            accepted=True,
            reason="LLM proposal accepted as augmentation proposal only",
        )
        return result

    def _call_provider(
        self,
        llm_input: LLMPlannerInput,
        request: AgentRequest,
        tool_catalog: list[ToolContract],
    ) -> LLMProviderResult:
        if self._proposal_provider is not None:
            return self._proposal_provider(llm_input, request)

        options = request.options
        backend = options.backend if options else "auto"
        model_id = self._requested_model_id(request)
        return self._model_router.generate(
            prompt=build_model_prompt(llm_input, tool_catalog),
            backend=backend,
            model_id=model_id,
        )

    @staticmethod
    def _requested_model_id(request: AgentRequest) -> str | None:
        if request.augmentation and request.augmentation.model_id:
            return request.augmentation.model_id

        options = request.options
        return options.model_id if options else None

    @staticmethod
    def _normalize_provider_result(
        provider_result: LLMProviderResult,
    ) -> tuple[str, dict[str, JsonValue] | None]:
        if isinstance(provider_result, str):
            return provider_result, None

        raw_output = provider_result.get("output")
        if not isinstance(raw_output, str):
            raise ValueError("ModelRouter result must include string output")
        return raw_output, dict(provider_result)

    def _record_trace(
        self,
        *,
        llm_input: LLMPlannerInput,
        result: AugmentationResult,
        accepted: bool,
        reason: str,
    ) -> None:
        self._audit_records.append(
            LLMAugmentationTrace(
                llm_input=llm_input,
                raw_output=result.raw_output,
                validated_output=(
                    result.model_dump(mode="json") if accepted else None
                ),
                model_router=result.model_router,
                accepted=accepted,
                reason=reason,
                fallback_reason=result.fallback_reason,
            )
        )
