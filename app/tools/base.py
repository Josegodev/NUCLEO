"""
NUCLEO - BASE TOOL

Define la interfaz común que deben implementar todas las tools.
"""
class BaseTool:
    name: str
    description: str
    read_only: bool
    risk_level: str

    def run(self, payload: dict) -> dict:
        raise NotImplementedError