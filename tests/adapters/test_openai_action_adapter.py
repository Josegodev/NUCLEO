import json
import pytest
from pydantic import ValidationError

from app.adapters.openai_action_adapter import parse_llm_output


def test_parse_valid_llm_output():
    raw = json.dumps({
        "tool_name": "echo",
        "payload": {"text": "hola"},
        "confidence": 0.9,
    })

    req = parse_llm_output(raw)

    assert req.tool_name == "echo"
    assert req.payload == {"text": "hola"}
    assert req.confidence == 0.9


def test_parse_rejects_invalid_json():
    with pytest.raises(ValueError):
        parse_llm_output("not-json")


def test_parse_rejects_invalid_schema():
    raw = json.dumps({
        "tool_name": "echo",
        "payload": {"text": "hola"},
        "confidence": 2.0,
    })

    with pytest.raises(ValidationError):
        parse_llm_output(raw)