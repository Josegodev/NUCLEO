import json

from app.domain.contracts.action_request import ActionRequest


def parse_llm_output(raw_output: str) -> ActionRequest:
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON from LLM output") from exc

    return ActionRequest.model_validate(payload)
