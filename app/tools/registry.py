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
- No evita sobrescritura de tools con mismo nombre
- No valida tipos estrictamente
- No incluye metadata adicional de tools

Arquitectura:
Patrón Service Locator dentro del pipeline:
planner → registry → policy → tool
"""

from app.tools.base import BaseTool
from app.tools.local.disk_info_tool import DiskInfoTool
from app.tools.local.echo_tool import EchoTool
from app.tools.local.system_info_tool import SystemInfoTool


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> BaseTool | None:
        return self._tools.get(tool_name)

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())


registry = ToolRegistry()
registry.register(EchoTool())
registry.register(SystemInfoTool())
registry.register(DiskInfoTool())
