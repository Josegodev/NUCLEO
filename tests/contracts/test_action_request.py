# tests/contracts/test_action_request.py

import pytest
from pydantic import ValidationError
from app.domain.contracts.action_request import ActionRequest

def test_valid_action_request():
    req = ActionRequest(
        tool_name="echo",
        payload={"text": "hola"},
        confidence=0.9,
    )
    assert req.tool_name == "echo"


def test_reject_extra_fields():
    with pytest.raises(ValidationError):
        ActionRequest(
            tool_name="echo",
            payload={"text": "hola"},
            confidence=0.9,
            extra="boom",
        )


def test_reject_invalid_confidence():
    with pytest.raises(ValidationError):
        ActionRequest(
            tool_name="echo",
            payload={"text": "hola"},
            confidence=2.0,
        )
