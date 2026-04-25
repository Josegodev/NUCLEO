#!/usr/bin/env python3
"""Export stable NUCLEO documentation for external LLM observation.

This script is intentionally outside app/. It reads documentation only and
writes static snapshots for local model review. It must not import or call
AgentService, Runtime, Planner, PolicyEngine, ToolRegistry, or Tools.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT = "NUCLEO"
PHASE = "HARDENING"
ALLOWED_LLM_ROLE = "external_observer_only"
ARCHITECTURE_FLOW = [
    "API",
    "AgentService",
    "AgentRuntime",
    "Planner",
    "PolicyEngine",
    "ToolRegistry",
    "Tool",
]
FORBIDDEN_ACTIONS = [
    "execute_tools",
    "modify_runtime",
    "bypass_policy",
    "call_agent_api",
]
OPEN_HARDENING_TOPICS = [
    "closed policy decisions",
    "dry_run determinism",
    "structured AgentResponse",
    "policy/registry consistency",
    "error handling",
    "observability",
]
STATIC_CONTEXT_FILES = [
    "README.md",
    "docs/architecture.md",
    "docs/operations/operational_state.md",
    "docs/operations/session_log.md",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def stable_context_paths(root: Path) -> list[Path]:
    paths = [root / relative_path for relative_path in STATIC_CONTEXT_FILES]
    modules_dir = root / "docs" / "modules"
    if modules_dir.exists():
        paths.extend(sorted(modules_dir.glob("*.md")))
    return [path for path in paths if path.exists() and path.is_file()]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def file_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_markdown(root: Path, generated_at: str, files: list[dict[str, object]]) -> str:
    lines = [
        "# NUCLEO Context Snapshot",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Scope",
        "",
        "- Project: NUCLEO",
        "- Phase: HARDENING",
        "- LLM role: external observer only",
        "- Runtime integration: none",
        "- Forbidden actions: execute tools, modify runtime, bypass policy, call agent API",
        "",
        "## Architecture Flow",
        "",
        "API -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> Tool",
        "",
        "## Open HARDENING Topics",
        "",
    ]
    lines.extend(f"- {topic}" for topic in OPEN_HARDENING_TOPICS)
    lines.extend(["", "## Files Included", ""])
    lines.extend(
        f"- `{item['path']}` ({item['bytes']} bytes, sha256: `{item['sha256']}`)"
        for item in files
    )
    lines.extend(["", "## Context", ""])

    for item in files:
        path = root / str(item["path"])
        lines.extend(
            [
                f"### {item['path']}",
                "",
                "```text",
                read_text(path),
                "```",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> None:
    root = repo_root()
    output_dir = root / "llm_context"
    output_dir.mkdir(exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    files: list[dict[str, object]] = []

    for path in stable_context_paths(root):
        text = read_text(path)
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": len(text.encode("utf-8")),
                "sha256": file_hash(text),
            }
        )

    payload = {
        "project": PROJECT,
        "phase": PHASE,
        "generated_at": generated_at,
        "architecture_flow": ARCHITECTURE_FLOW,
        "allowed_llm_role": ALLOWED_LLM_ROLE,
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "open_hardening_topics": OPEN_HARDENING_TOPICS,
        "files": files,
    }

    json_path = output_dir / "nucleo_context_snapshot.json"
    markdown_path = output_dir / "nucleo_context_snapshot.md"

    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        build_markdown(root, generated_at, files),
        encoding="utf-8",
    )

    print(f"Wrote {json_path.relative_to(root)}")
    print(f"Wrote {markdown_path.relative_to(root)}")


if __name__ == "__main__":
    main()
