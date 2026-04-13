"""
NUCLEO - BASE TOOL

Define la interfaz común que deben implementar todas las tools.

Contrato:
- Todas las tools deben implementar run(payload, context)
- El context contiene información de ejecución (usuario, request_id, etc.)
- Las tools NO deben encargarse de autenticación ni autorización
"""

from app.schemas.context import ExecutionContext


class BaseTool:
    name: str
    description: str
    read_only: bool
    risk_level: str

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        raise NotImplementedError