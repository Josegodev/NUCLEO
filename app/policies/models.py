from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PolicyDecisionValue(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class PolicyValidatedField(str, Enum):
    AUTHENTICATED_CONTEXT = "authenticated_context"
    TOOL_NAME = "tool_name"
    TOOL_REGISTERED = "tool_registered"
    PAYLOAD = "payload"
    DRY_RUN = "dry_run"
    ROLE = "role"


class PolicyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    decision: PolicyDecisionValue
    reason: str = Field(min_length=1)
    validated_fields: list[PolicyValidatedField] = Field(min_length=1)
    version: Literal["policy_decision.v1"] = "policy_decision.v1"
