import os
import platform
import shutil

from app.schemas.context import ExecutionContext
from app.tools.base import BaseTool


class DiskInfoTool(BaseTool):
    """Return disk usage information for a path or mount point.

    This tool reports disk usage, not RAM or any other memory metric.

    Cross-platform behavior:
    - Uses ``platform.system()`` to detect the current operating system.
    - Defaults to ``"C:\\"`` on Windows when no path is provided.
    - Defaults to ``"/"`` on Linux and macOS when no path is provided.
    - Works with paths and mount points supported by the host OS.

    Limitations:
    - Does not distinguish disk type.
    - Does not enumerate multiple disks.
    - Does not measure RAM.
    """

    name = "disk_info"
    description = "Returns disk usage information for a path or mount point."
    read_only = True
    risk_level = "low"

    def run(self, payload: dict | None = None, context: ExecutionContext | None = None) -> dict:
        payload = payload or {}

        try:
            system_name = platform.system()
            requested_path = payload.get("path")
            target_path = requested_path or self._default_path(system_name)

            if not os.path.exists(target_path):
                return self._error_response(f"Path does not exist: {target_path}", target_path, system_name)

            usage = shutil.disk_usage(target_path)
            total_gb = self._bytes_to_gb(usage.total)
            used_gb = self._bytes_to_gb(usage.used)
            free_gb = self._bytes_to_gb(usage.free)
            free_percent = round((usage.free / usage.total) * 100, 2) if usage.total else 0.0

            return {
                "status": "ok",
                "message": f"Disk usage retrieved successfully for path: {target_path}",
                "data": {
                    "path": target_path,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "total_gb": total_gb,
                    "used_gb": used_gb,
                    "free_gb": free_gb,
                    "free_percent": free_percent,
                    "os": system_name,
                    "platform_details": platform.platform(),
                },
            }
        except Exception as exc:
            system_name = platform.system()
            target_path = payload.get("path") or self._default_path(system_name)
            return self._error_response(str(exc), target_path, system_name)

    def _default_path(self, system_name: str) -> str:
        return "C:\\" if system_name == "Windows" else "/"

    def _bytes_to_gb(self, value: int) -> float:
        return round(value / (1024**3), 2)

    def _error_response(self, message: str, path: str, system_name: str) -> dict:
        return {
            "status": "error",
            "message": message,
            "data": {
                "path": path,
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "total_gb": 0.0,
                "used_gb": 0.0,
                "free_gb": 0.0,
                "free_percent": 0.0,
                "os": system_name,
                "platform_details": platform.platform(),
            },
        }
