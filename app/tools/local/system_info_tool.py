import platform
import socket

from app.schemas.context import ExecutionContext
from app.schemas.artifacts import (
    SystemInfoOutput,
    SystemInfoPayload,
    ToolContractArtifact,
    ToolPostcondition,
    ToolPrecondition,
    ToolSideEffect,
)
from app.tools.base import BaseTool


class SystemInfoTool(BaseTool):
    name = "system_info"
    description = "Returns basic information about the local system."
    read_only = True
    risk_level = "low"
    contract = ToolContractArtifact(
        name="system_info",
        input_schema=SystemInfoPayload.model_json_schema(),
        output_schema=SystemInfoOutput.model_json_schema(),
        preconditions=[
            ToolPrecondition.AUTHENTICATED_CONTEXT,
            ToolPrecondition.PAYLOAD_VALIDATED,
        ],
        postconditions=[
            ToolPostcondition.STRUCTURED_OUTPUT,
            ToolPostcondition.OUTPUT_SCHEMA_VALIDATED,
        ],
        side_effects=[ToolSideEffect.READ_SYSTEM_METADATA],
    )

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        return {
            "requested_by": context.username if context else None,
            "request_id": context.request_id if context else None,
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": socket.gethostname(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }
