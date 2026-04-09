from app.policies.models import PolicyDecision


class PolicyEngine:
    def evaluate(self, tool_name: str, payload: dict, dry_run: bool) -> PolicyDecision:
        if tool_name == "echo":
            return PolicyDecision(
                decision="allow",
                reason="echo tool is allowed"
            )

        return PolicyDecision(
            decision="deny",
            reason=f"tool '{tool_name}' is not allowed by policy"
        )