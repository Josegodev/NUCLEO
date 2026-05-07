"""
NUCLEO - TOOL REGISTRY

Catálogo central de herramientas disponibles en el sistema.

Responsable de:
- Registrar tools disponibles (BaseTool)
- Resolver tools por nombre
- Proporcionar acceso a las implementaciones de ejecución

Flujo:
tool_name (desde planner)
    → lookup en registry
    → instancia de tool
    → ejecución (tool.run)

Estructura interna:
dict[str, BaseTool]
{
    "tool_name": tool_instance
}

Funciones:
- register(tool): añade una tool al registro
- get(tool_name): obtiene una tool por nombre
- list_tools(): devuelve todas las tools registradas

Notas:
- Permite desacoplar runtime de implementaciones concretas
- Facilita la extensión sin modificar el núcleo
- Utiliza acceso O(1) mediante diccionario

Limitaciones actuales:
- No separa bootstrap-time registration de runtime lookup
- No incluye metadata operacional adicional de tools

	Arquitectura:
	Patrón Service Locator dentro del pipeline:
	planner → policy → registry → tool
"""

from app.tools.base import BaseTool
from app.tools.local.disk_info_tool import DiskInfoTool
from app.tools.local.echo_tool import EchoTool
from app.tools.local.system_info_tool import SystemInfoTool
from app.schemas.artifacts import KNOWN_TOOL_NAMES, ToolContractArtifact


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if not isinstance(tool, BaseTool):
            raise TypeError("registered tool must inherit BaseTool")

        contract = getattr(tool, "contract", None)
        if not isinstance(contract, ToolContractArtifact):
            raise TypeError(f"tool '{tool.name}' must expose a ToolContractArtifact")

        if tool.name not in KNOWN_TOOL_NAMES:
            raise ValueError(f"tool '{tool.name}' is outside the closed tool set")

        if contract.name != tool.name:
            raise ValueError(
                f"tool contract name '{contract.name}' does not match tool name '{tool.name}'"
            )

        if tool.name in self._tools:
            raise ValueError(f"tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> BaseTool | None:
        return self._tools.get(tool_name)

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def list_contracts(self) -> list[ToolContractArtifact]:
        return [tool.contract for tool in self.list_tools()]


registry = ToolRegistry()
registry.register(EchoTool())
registry.register(SystemInfoTool())
registry.register(DiskInfoTool())
