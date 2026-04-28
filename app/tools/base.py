"""
NUCLEO - BASE TOOL

Define la interfaz común que deben implementar todas las tools.

Contrato:
- Todas las tools deben implementar run(payload, context)
- El context contiene información de ejecución (usuario, request_id, etc.)
- Las tools NO deben encargarse de autenticación ni autorización
"""

from app.schemas.context import ExecutionContext
from app.schemas.artifacts import (
    StructuredData,
    ToolContractArtifact,
    validate_tool_output,
    validate_tool_payload,
)


class BaseTool:
    name: str
    description: str
    read_only: bool
    risk_level: str
    contract: ToolContractArtifact

    def validate_input(self, payload: dict | None = None) -> StructuredData:
        return validate_tool_payload(self.name, payload or {})

    def validate_output(self, output: dict) -> StructuredData:
        return validate_tool_output(self.name, output)

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        raise NotImplementedError
