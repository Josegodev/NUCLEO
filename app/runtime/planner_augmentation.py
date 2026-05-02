"""Backward-compatible Planner augmentation adapters.

The LLM boundary now lives in `augmentation_service.py`. This module keeps the
older imports used by tests and lab evals while delegating model calls and
validation to AugmentationService.
"""

from __future__ import annotations

from app.domain.tool_proposals.models import AgentActionProposal
from app.runtime.augmentation_service import (
    AugmentationResult,
    AugmentationService,
    LLMAugmentationTrace,
    LLMPlannerInput,
    LLMProposalProvider,
    ModelRouterProposalProvider,
    _strip_json_fence,
    build_augmentation_metadata,
    build_llm_input,
    build_tool_catalog_prompt,
    serialize_tool_catalog,
    validate_llm_proposal,
)
from app.runtime.planner import DeterministicPlannerStrategy, PlannerStrategy
from app.schemas.artifacts import JsonValue
from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentMode, AgentRequest
from app.tools.registry import ToolRegistry
from app.tools.registry import registry as default_registry


def build_tool_contract_prompt(tool_registry: ToolRegistry) -> str:
    return build_tool_catalog_prompt(serialize_tool_catalog(tool_registry))


class LLMPlanOutputValidator:
    def __init__(self, tool_registry: ToolRegistry = default_registry) -> None:
        self._tool_registry = tool_registry

    @property
    def tool_catalog(self):
        if hasattr(self._tool_registry, "list_contracts"):
            return serialize_tool_catalog(self._tool_registry)
        return serialize_tool_catalog(default_registry)

    def validate_raw_output(self, raw_output: str) -> AgentActionProposal:
        return validate_llm_proposal(raw_output, self.tool_catalog)

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
            return self._deterministic_fallback_plan(
                request,
                fallback_augmentation(reason),
            )

        service = AugmentationService(proposal_provider=self._proposal_provider)
        result = service.run(
            request=request,
            context=None,
            tool_catalog=self._validator.tool_catalog,
        )
        self._audit_records.extend(service.audit_records)

        if result.fallback_used:
            return self._deterministic_fallback_plan(request, result)

        return self._plan_from_augmentation_result(result, request)

    @staticmethod
    def _build_llm_input(request: AgentRequest) -> LLMPlannerInput:
        return build_llm_input(request)

    def _should_attempt_augmentation(self, request: AgentRequest) -> bool:
        return (
            self._enabled
            and request.options is not None
            and request.agent_mode == AgentMode.PROPOSAL_ONLY
        )

    def _deterministic_fallback_plan(
        self,
        request: AgentRequest,
        augmentation_result: AugmentationResult,
    ) -> PlannedAction:
        plan = self._deterministic_strategy.create_plan(request)
        metadata = build_augmentation_metadata(
            augmentation_result,
            request=request,
            fallback_plan=plan,
        )
        return plan.model_copy(update={"metadata": metadata})

    @staticmethod
    def _plan_from_augmentation_result(
        result: AugmentationResult,
        request: AgentRequest,
    ) -> PlannedAction:
        metadata = build_augmentation_metadata(result, request=request)
        proposed_action = result.proposed_action
        if proposed_action is None:
            return PlannedAction(
                payload={},
                status="no_plan",
                confidence=0.0,
                reason=f"LLM-assisted proposal returned no action: {result.assistant_message}",
                source="llm_assisted",
                metadata=metadata,
            )

        return PlannedAction(
            tool_name=proposed_action.tool_name,
            payload=proposed_action.arguments,
            status="planned",
            confidence=proposed_action.confidence,
            reason=f"LLM-assisted proposal accepted: {result.assistant_message}",
            source="llm_assisted",
            metadata=metadata,
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


def fallback_augmentation(reason: str) -> AugmentationResult:
    return AugmentationResult(
        mode="proposal",
        assistant_message="Deterministic fallback used.",
        proposed_action=None,
        fallback_used=True,
        fallback_reason=reason,
        validation_errors=[reason],
    )
