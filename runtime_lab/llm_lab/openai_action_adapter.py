def to_action_request(llm_output: str) -> dict:
    # parseo estricto
    return {
        "tool_name": "echo",
        "payload": {"text": "hola nucleo"}
    }