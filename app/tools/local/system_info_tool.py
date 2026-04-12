import platform
import socket

from app.tools.base import BaseTool


class SystemInfoTool(BaseTool):
    name = "system_info"
    description = "Returns basic information about the local system."
    read_only = True
    risk_level = "low"

    def run(self, payload: dict) -> dict:
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": socket.gethostname(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }