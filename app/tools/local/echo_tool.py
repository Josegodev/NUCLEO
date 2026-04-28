from app.schemas.context import ExecutionContext
from app.schemas.artifacts import (
    EchoOutput,
    EchoPayload,
    ToolContractArtifact,
    ToolPostcondition,
    ToolPrecondition,
    ToolSideEffect,
)
from app.tools.base import BaseTool


class EchoTool(BaseTool):
    name = "echo"
    description = "A simple tool that returns the payload it receives."
    read_only = True
    risk_level = "low"
    contract = ToolContractArtifact(
        name="echo",
        input_schema=EchoPayload.model_json_schema(),
        output_schema=EchoOutput.model_json_schema(),
        preconditions=[
            ToolPrecondition.AUTHENTICATED_CONTEXT,
            ToolPrecondition.PAYLOAD_VALIDATED,
        ],
        postconditions=[
            ToolPostcondition.STRUCTURED_OUTPUT,
            ToolPostcondition.OUTPUT_SCHEMA_VALIDATED,
        ],
        side_effects=[ToolSideEffect.NONE],
    )

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        return {
            "echo": payload,
            "requested_by": context.username if context else None,
            "request_id": context.request_id if context else None,
        }
