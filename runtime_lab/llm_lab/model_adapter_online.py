from app.contracts.action_request import ActionRequest

def parse_llm_output(raw: str) -> ActionRequest:
    data = json.loads(raw)
    return ActionRequest(**data)  # aquí rompe si no cumple