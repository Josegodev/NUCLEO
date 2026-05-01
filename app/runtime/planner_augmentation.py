"""
Controlled LLM-assisted planning primitives.

This module is the only Planner augmentation boundary. It can ask a model for a
structured proposal, but it cannot execute tools, authorize actions, or mutate
the production ToolRegistry.
"""

from __future__ import annotations

import json
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.adapters.model_router import ModelRouter
from app.domain.tool_proposals.models import AgentActionProposal
from app.runtime.planner import DeterministicPlannerStrategy, PlannerStrategy
from app.schemas.artifacts import JsonValue, ToolName, ensure_known_tool_name
from app.schemas.artifacts import validate_tool_payload
from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentMode, AgentRequest
from app.tools.registry import ToolRegistry
from app.tools.registry import registry as default_registry


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


def build_tool_contract_prompt(tool_registry: ToolRegistry) -> str:
    lines = [
        "Available tools and required argument schemas:",
        "",
    ]

    for contract in sorted(tool_registry.list_contracts(), key=lambda item: item.name):
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


class LLMPlanOutputValidator:
    def __init__(self, tool_registry: ToolRegistry = default_registry) -> None:
        self._tool_registry = tool_registry

    def validate_raw_output(self, raw_output: str) -> AgentActionProposal:
        try:
            decoded_output = json.loads(_strip_json_fence(raw_output))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid JSON from LLM output") from exc

        proposal = self._validate_shape(decoded_output)
        if proposal.suggested_action is None:
            return proposal

        tool_name = self._validate_tool_name(proposal.suggested_action)

        if self._tool_registry.get(tool_name) is None:
            raise ValueError(f"LLM referenced unregistered tool: {tool_name}")

        try:
            validated_payload = validate_tool_payload(tool_name, proposal.arguments)
        except (TypeError, ValueError, ValidationError) as exc:
            raise ValueError(
                f"LLM payload does not match tool contract for "
                f"'{tool_name}': {exc}"
            ) from exc

        return AgentActionProposal(
            intent=proposal.intent,
            suggested_action=tool_name,
            arguments=validated_payload,
            confidence=proposal.confidence,
        )

    def to_planned_action(
        self,
        proposal: AgentActionProposal,
        metadata: dict[str, JsonValue] | None = None,
    ) -> PlannedAction:
        if proposal.suggested_action is None:
            return PlannedAction(
                payload={},
                status="no_plan",
                confidence=proposal.confidence,
                reason=f"LLM-assisted proposal returned no action: {proposal.intent}",
                source="llm_assisted",
                metadata=metadata or {},
            )

        return PlannedAction(
            tool_name=proposal.suggested_action,
            payload=proposal.arguments,
            status="planned",
            confidence=proposal.confidence,
            reason=f"LLM-assisted proposal accepted: {proposal.intent}",
            source="llm_assisted",
            metadata=metadata or {},
        )

    @staticmethod
    def _validate_shape(decoded_output: object) -> AgentActionProposal:
        if not isinstance(decoded_output, dict):
            raise ValueError("LLM output must be a JSON object")

        intent = LLMPlanOutputValidator._required_string(decoded_output, "intent")
        suggested_action_value = decoded_output.get("suggested_action")
        if suggested_action_value is None:
            suggested_action = None
        else:
            suggested_action = LLMPlanOutputValidator._required_string(
                decoded_output,
                "suggested_action",
            )
        arguments = decoded_output.get("arguments")
        if not isinstance(arguments, dict):
            raise ValueError("LLM output field 'arguments' must be an object")
        if suggested_action is None and arguments:
            raise ValueError(
                "LLM output with suggested_action=null must use empty arguments"
            )

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

    @staticmethod
    def _required_string(payload: dict, field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"LLM output field '{field_name}' must be a string")
        return value.strip()

    @staticmethod
    def _validate_tool_name(tool_name: str) -> ToolName:
        try:
            return ensure_known_tool_name(tool_name)
        except ValueError as exc:
            raise ValueError(f"LLM referenced unknown tool: {tool_name}") from exc


LLMProviderResult = str | dict[str, JsonValue]
LLMProposalProvider = Callable[[LLMPlannerInput, AgentRequest], LLMProviderResult]


class ModelRouterProposalProvider:
    def __init__(
        self,
        model_router: ModelRouter | None = None,
        tool_registry: ToolRegistry = default_registry,
    ) -> None:
        self._model_router = model_router or ModelRouter()
        self._tool_registry = tool_registry

    def __call__(
        self,
        llm_input: LLMPlannerInput,
        request: AgentRequest,
    ) -> dict[str, JsonValue]:
        options = request.options
        backend = options.backend if options else "auto"
        model_id = options.model_id if options else None
        return self._model_router.generate(
            prompt=self._build_prompt(llm_input),
            backend=backend,
            model_id=model_id,
        )

    def _build_prompt(self, llm_input: LLMPlannerInput) -> str:
        return "\n".join(
            [
                "You are augmenting the NUCLEO Planner.",
                "Return JSON only, with exactly these fields:",
                '{"intent": string, "suggested_action": string | null, "arguments": object, "confidence": number}',
                build_tool_contract_prompt(self._tool_registry),
                "Do not execute tools.",
                "Do not authorize actions.",
                "The PolicyEngine and ToolRegistry will validate the proposal.",
                f"Goal: {llm_input.goal}",
                f"Context: {json.dumps(llm_input.context, ensure_ascii=True)}",
                f"Constraints: {json.dumps(llm_input.constraints, ensure_ascii=True)}",
            ]
        )


class LLMAssistedPlannerStrategy:
    def __init__(
        self,
        deterministic_strategy: PlannerStrategy | None = None,
        proposal_provider: LLMProposalProvider | None = None,
        validator: LLMPlanOutputValidator | None = None,
        enabled: bool = False,
    ) -> None:
        self._deterministic_strategy = (
            deterministic_strategy or DeterministicPlannerStrategy()
        )
        self._proposal_provider = proposal_provider
        self._validator = validator or LLMPlanOutputValidator()
        self._enabled = enabled
        self._audit_records: list[LLMAugmentationTrace] = []

    @property
    def audit_records(self) -> list[LLMAugmentationTrace]:
        return list(self._audit_records)

    def create_plan(self, request: AgentRequest) -> PlannedAction:
        llm_input = self._build_llm_input(request)

        if not self._should_attempt_augmentation(request):
            self._record_rejection(
                llm_input=llm_input,
                raw_output=None,
                model_router=None,
                reason="llm_assisted disabled or not requested; deterministic fallback used",
            )
            return self._deterministic_strategy.create_plan(request)

        if self._proposal_provider is None:
            reason = "no LLM proposal provider configured; deterministic fallback used"
            self._record_rejection(
                llm_input=llm_input,
                raw_output=None,
                model_router=None,
                reason=reason,
            )
            return self._deterministic_fallback_plan(request, None, None, reason)

        raw_output: str | None = None
        router_result: dict[str, JsonValue] | None = None
        try:
            provider_result = self._proposal_provider(llm_input, request)
            raw_output, router_result = self._normalize_provider_result(
                provider_result
            )
            proposal = self._validator.validate_raw_output(raw_output)
            metadata = self._metadata(
                proposal=proposal,
                raw_output=raw_output,
                router_result=router_result,
                fallback_reason=None,
                request=request,
            )
            plan = self._validator.to_planned_action(proposal, metadata=metadata)
        except Exception as exc:
            reason = f"LLM proposal rejected; deterministic fallback used: {exc}"
            self._record_rejection(
                llm_input=llm_input,
                raw_output=raw_output,
                model_router=router_result,
                reason=reason,
            )
            return self._deterministic_fallback_plan(
                request,
                raw_output,
                router_result,
                reason,
            )

        self._audit_records.append(
            LLMAugmentationTrace(
                llm_input=llm_input,
                raw_output=raw_output,
                validated_output=self._proposal_to_dict(proposal),
                model_router=router_result,
                accepted=True,
                reason="LLM proposal accepted as Planner proposal only",
                fallback_reason=None,
            )
        )
        return plan

    @staticmethod
    def _build_llm_input(request: AgentRequest) -> LLMPlannerInput:
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

        return LLMPlannerInput(
            goal=request.user_input or "",
            context=context,
            constraints=[
                "Return valid JSON only.",
                "Use fields: intent, suggested_action, arguments, confidence.",
                "Propose tools only; never execute tools.",
                "Use registered tools only.",
                "PolicyEngine remains the final authority before execution.",
                "ToolRegistry must not be modified.",
                "dry_run remains true for Productive Agent Console v0.",
            ],
        )

    def _should_attempt_augmentation(self, request: AgentRequest) -> bool:
        return (
            self._enabled
            and request.options is not None
            and request.options.agent_mode == AgentMode.PROPOSAL_ONLY
        )

    def _deterministic_fallback_plan(
        self,
        request: AgentRequest,
        raw_output: str | None,
        router_result: dict[str, JsonValue] | None,
        fallback_reason: str,
    ) -> PlannedAction:
        plan = self._deterministic_strategy.create_plan(request)
        proposal = self._proposal_from_plan(plan)
        metadata = self._metadata(
            proposal=proposal,
            raw_output=raw_output,
            router_result=router_result,
            fallback_reason=fallback_reason,
            request=request,
        )
        return plan.model_copy(update={"metadata": metadata})

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

    @staticmethod
    def _metadata(
        proposal: AgentActionProposal,
        raw_output: str | None,
        router_result: dict[str, JsonValue] | None,
        fallback_reason: str | None,
        request: AgentRequest | None = None,
    ) -> dict[str, JsonValue]:
        metadata: dict[str, JsonValue] = {
            "augmentation_attempted": True,
            "proposal": LLMAssistedPlannerStrategy._proposal_to_dict(proposal),
            "model_output": raw_output or "",
            "fallback_used": fallback_reason is not None,
            "fallback_reason": fallback_reason,
        }
        if request and request.options:
            metadata["backend"] = request.options.backend.value
            metadata["model_id"] = request.options.model_id
        if router_result:
            for key in (
                "model_used",
                "backend_used",
                "latency_ms",
                "fallback_used",
                "fallback_reason",
            ):
                if key in router_result:
                    metadata[key] = router_result[key]
            if fallback_reason is not None:
                metadata["fallback_used"] = True
                router_reason = router_result.get("fallback_reason")
                if isinstance(router_reason, str) and router_reason:
                    metadata["fallback_reason"] = f"{router_reason}; {fallback_reason}"
                else:
                    metadata["fallback_reason"] = fallback_reason
        return metadata

    @staticmethod
    def _proposal_to_dict(proposal: AgentActionProposal) -> dict[str, JsonValue]:
        return {
            "intent": proposal.intent,
            "suggested_action": proposal.suggested_action,
            "arguments": proposal.arguments,
            "confidence": proposal.confidence,
        }

    @staticmethod
    def _proposal_from_plan(plan: PlannedAction) -> AgentActionProposal:
        return AgentActionProposal(
            intent=plan.reason,
            suggested_action=plan.tool_name or "no_plan",
            arguments=plan.payload,
            confidence=plan.confidence,
        )

    def _record_rejection(
        self,
        llm_input: LLMPlannerInput,
        raw_output: str | None,
        model_router: dict[str, JsonValue] | None,
        reason: str,
    ) -> None:
        self._audit_records.append(
            LLMAugmentationTrace(
                llm_input=llm_input,
                raw_output=raw_output,
                validated_output=None,
                model_router=model_router,
                accepted=False,
                reason=reason,
                fallback_reason=reason,
            )
        )
