from pydantic import BaseModel


class PolicyDecision(BaseModel):
    decision: str
    reason: str