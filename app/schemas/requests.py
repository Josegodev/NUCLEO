from enum import Enum
from typing import Any

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class AgentBackend(str, Enum):
    LOCAL = "local"
    OPENAI = "openai"
    AUTO = "auto"


class AgentMode(str, Enum):
    PROPOSAL_ONLY = "proposal_only"


class AgentRunOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: AgentBackend = AgentBackend.AUTO
    model_id: str = Field(default="llama3.1:8b", min_length=1)
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
    tool: str | None = None
    payload: dict[str, Any] | None = None
    dry_run: bool = True
    experimental_tool_generation: bool = False

    @model_validator(mode="after")
    def apply_agent_console_options(self) -> "AgentRequest":
        if self.options is not None:
            self.dry_run = self.options.dry_run
        return self
