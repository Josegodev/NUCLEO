from enum import Enum
from typing import Any

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_validator,
    model_validator,
)


class AgentBackend(str, Enum):
    LOCAL = "local"
    OPENAI = "openai"
    AUTO = "auto"


class AgentMode(str, Enum):
    PROPOSAL_ONLY = "proposal_only"


DEFAULT_AUGMENTATION_MODEL_ID = "llama3.1:8b"
ALLOWED_AUGMENTATION_MODELS = frozenset(
    {
        "qwen",
        "mistral",
        DEFAULT_AUGMENTATION_MODEL_ID,
    }
)


def resolve_augmentation_model_id(model_id: str | None) -> tuple[str, str | None]:
    requested_model = (model_id or "").strip()
    if not requested_model:
        return DEFAULT_AUGMENTATION_MODEL_ID, None

    if requested_model in ALLOWED_AUGMENTATION_MODELS:
        return requested_model, None

    return (
        DEFAULT_AUGMENTATION_MODEL_ID,
        (
            f"model_id '{requested_model}' is not allowed; "
            f"using default model '{DEFAULT_AUGMENTATION_MODEL_ID}'"
        ),
    )


class AugmentationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str | None = None

    @field_validator("model_id")
    @classmethod
    def blank_model_id_uses_default(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None
        return normalized


class AgentRunOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: AgentBackend = AgentBackend.AUTO
    model_id: str = Field(default=DEFAULT_AUGMENTATION_MODEL_ID, min_length=1)
    agent_mode: AgentMode = AgentMode.PROPOSAL_ONLY
    dry_run: bool = True

    @field_validator("model_id")
    @classmethod
    def model_id_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("model_id must not be blank")
        return normalized

    @model_validator(mode="after")
    def force_dry_run_for_proposal_only(self) -> "AgentRunOptions":
        if self.agent_mode == AgentMode.PROPOSAL_ONLY:
            self.dry_run = True
        return self


class AgentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    user_input: str | None = Field(
        default=None,
        validation_alias=AliasChoices("user_input", "input"),
    )
    context: dict[str, Any] = Field(default_factory=dict)
    options: AgentRunOptions | None = None
    agent_mode: AgentMode | None = None
    augmentation: AugmentationRequest | None = None
    tool: str | None = None
    payload: dict[str, Any] | None = None
    dry_run: bool = True
    experimental_tool_generation: bool = False

    _model_resolution_reason: str | None = PrivateAttr(default=None)

    @property
    def model_resolution_reason(self) -> str | None:
        return self._model_resolution_reason

    @model_validator(mode="after")
    def apply_agent_console_options(self) -> "AgentRequest":
        option_updates: dict[str, Any] = {}
        if self.agent_mode is not None:
            option_updates["agent_mode"] = self.agent_mode
        if self.augmentation is not None and self.augmentation.model_id is not None:
            model_id, reason = resolve_augmentation_model_id(
                self.augmentation.model_id
            )
            self.augmentation = self.augmentation.model_copy(
                update={"model_id": model_id}
            )
            self._model_resolution_reason = reason
            option_updates["model_id"] = model_id

        if self.options is None and (self.agent_mode is not None or self.augmentation is not None):
            self.options = AgentRunOptions(
                dry_run=self.dry_run,
                **option_updates,
            )
        elif self.options is not None and option_updates:
            self.options = AgentRunOptions.model_validate(
                {
                    **self.options.model_dump(),
                    **option_updates,
                }
            )

        if self.options is not None:
            self.agent_mode = self.options.agent_mode
            self.dry_run = self.options.dry_run
        return self
