import platform
import socket

from app.schemas.context import ExecutionContext
from app.tools.base import BaseTool


class SystemInfoTool(BaseTool):
    name = "system_info"
    description = "Returns basic information about the local system."
    read_only = True
    risk_level = "low"

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