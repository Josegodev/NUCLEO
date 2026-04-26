from typing import Literal

from pydantic import BaseModel


class PolicyDecision(BaseModel):
    decision: Literal["allow", "deny"]
    reason: str
