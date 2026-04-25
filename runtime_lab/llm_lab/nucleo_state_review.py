#!/usr/bin/env python3
"""Build a bounded HARDENING review prompt from the NUCLEO repository.

This script is intentionally outside NUCLEO's app/ runtime. It reads selected
files, creates a traceable markdown report, and leaves local LLM execution as a
clear replaceable stub.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ALLOWED_ROOTS = (
    "docs",
    "docs_esp",
    "app/runtime",
    "app/planner",
    "app/policies",
    "app/tools",
    "tests",
)
ALLOWED_FILES = ("README.md",)
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "databases",
    "modelos",
}
EXCLUDED_SUFFIXES = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pyc",
    ".pyo",
    ".log",
}
DEFAULT_CONTEXT_LIMIT_CHARS = 120_000
REPORTS_DIR = Path(__file__).resolve().parent / "reports"


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    relative_path: str
    size_bytes: int
    sha256_12: str
    content: str


def resolve_repo_path() -> Path:
    """Resolve NUCLEO_REPO_PATH and fail early if it is not usable."""
    raw_path = os.environ.get("NUCLEO_REPO_PATH")
    if not raw_path:
        raise RuntimeError("NUCLEO_REPO_PATH is required")

    repo_path = Path(raw_path).expanduser().resolve()
    if not repo_path.exists():
        raise RuntimeError(f"NUCLEO_REPO_PATH does not exist: {repo_path}")
    if not repo_path.is_dir():
        raise RuntimeError(f"NUCLEO_REPO_PATH is not a directory: {repo_path}")
    return repo_path


def is_allowed(relative_path: Path) -> bool:
    """Return True only for the explicitly allowed NUCLEO paths."""
    as_posix = relative_path.as_posix()
    if as_posix in ALLOWED_FILES:
        return True
    return any(as_posix == root or as_posix.startswith(f"{root}/") for root in ALLOWED_ROOTS)


def is_excluded(path: Path, relative_path: Path) -> bool:
    """Filter caches, VCS data, databases, model folders, and heavy logs."""
    parts = set(relative_path.parts)
    if parts & EXCLUDED_PARTS:
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    return False


def discover_files(repo_path: Path) -> list[Path]:
    """Collect allowed files in deterministic order."""
    files: list[Path] = []
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(repo_path)
        if is_excluded(path, relative_path):
            continue
        if is_allowed(relative_path):
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(repo_path).as_posix())


def read_snapshot(repo_path: Path, path: Path) -> FileSnapshot:
    """Read one text file and calculate a short content hash."""
    raw = path.read_bytes()
    relative_path = path.relative_to(repo_path).as_posix()
    content_hash = hashlib.sha256(raw).hexdigest()[:12]
    text = raw.decode("utf-8", errors="replace")
    return FileSnapshot(
        path=path,
        relative_path=relative_path,
        size_bytes=len(raw),
        sha256_12=content_hash,
        content=text,
    )


def build_context(snapshots: list[FileSnapshot], limit_chars: int) -> tuple[str, bool]:
    """Build a bounded, traceable context block."""
    chunks: list[str] = []
    total_chars = 0
    truncated = False

    for snapshot in snapshots:
        header = (
            f"\n\n--- FILE: {snapshot.relative_path} "
            f"| bytes={snapshot.size_bytes} "
            f"| sha256_12={snapshot.sha256_12} ---\n"
        )
        block = header + snapshot.content
        if total_chars + len(block) > limit_chars:
            remaining = max(limit_chars - total_chars, 0)
            if remaining > len(header):
                chunks.append(header + snapshot.content[: remaining - len(header)])
            truncated = True
            break
        chunks.append(block)
        total_chars += len(block)

    return "".join(chunks).strip(), truncated


def build_hardening_prompt(context: str, truncated: bool) -> str:
    """Create the base prompt used for the external HARDENING audit."""
    truncation_note = "yes" if truncated else "no"
    return f"""You are reviewing the current NUCLEO repository state.

Scope:
- This is an external llm_lab review path, not part of NUCLEO runtime.
- Do not propose LLM integration into AgentService, Runtime, Planner, PolicyEngine, ToolRegistry, or Tools.
- Do not expand architecture.
- Focus on HARDENING only.

Review goals:
- Contracts between PolicyDecision, PolicyEngine, runtime/orchestrator, and ToolRegistry.
- Determinism in execution.
- Explicit validation.
- Error handling.
- Tests.
- Documentation consistency.

Output rules:
- Classify each finding as CRITICAL, INFORMATIVE, or PREMATURE.
- Point to exact files from the provided context.
- Prefer the smallest reasonable change.
- If evidence is missing, say so.

Context truncated: {truncation_note}

NUCLEO CONTEXT:
{context}
"""


def call_local_llm(prompt: str) -> str:
    """Stub for a future local model call.

    Replace this body with a call to llm_lab/qwen or llm_lab/mistral only when
    you deliberately want to execute a local model. Keeping this as a stub
    prevents accidental runtime coupling.
    """
    _ = prompt
    return (
        "LOCAL_LLM_NOT_CALLED\n\n"
        "The HARDENING prompt was generated successfully, but this script did "
        "not call a local model yet. Wire this function to a local llm_lab "
        "model runner when you want that behavior."
    )


def render_report(
    repo_path: Path,
    generated_at: datetime,
    snapshots: list[FileSnapshot],
    context: str,
    prompt: str,
    llm_output: str,
    truncated: bool,
) -> str:
    """Render a markdown report with traceable inputs and output."""
    total_size = sum(snapshot.size_bytes for snapshot in snapshots)
    files_table = "\n".join(
        f"| `{snapshot.relative_path}` | {snapshot.size_bytes} | `{snapshot.sha256_12}` |"
        for snapshot in snapshots
    )
    if not files_table:
        files_table = "| _No files read_ | 0 | _n/a_ |"

    return f"""# NUCLEO State Review

Generated at: {generated_at.isoformat(timespec="seconds")}

Repository: `{repo_path}`

## Summary

- Files read: {len(snapshots)}
- Total size: {total_size} bytes
- Context size: {len(context)} characters
- Context truncated: {"yes" if truncated else "no"}
- Execution path: external `llm_lab`
- Runtime integration: none

## Files Read

| File | Bytes | SHA-256 short |
| --- | ---: | --- |
{files_table}

## Local LLM Output

```text
{llm_output}
```

## Prompt Sent Or Prepared

```text
{prompt}
```
"""


def write_report(markdown: str, generated_at: datetime) -> Path:
    """Write the markdown report using the requested timestamp format."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_name = f"nucleo_state_review_{generated_at:%Y%m%d_%H%M}.md"
    report_path = REPORTS_DIR / report_name
    report_path.write_text(markdown, encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an external llm_lab HARDENING review report for NUCLEO."
    )
    parser.add_argument(
        "--context-limit-chars",
        type=int,
        default=DEFAULT_CONTEXT_LIMIT_CHARS,
        help=f"Maximum characters copied into the model context. Default: {DEFAULT_CONTEXT_LIMIT_CHARS}",
    )
    args = parser.parse_args()

    repo_path = resolve_repo_path()
    file_paths = discover_files(repo_path)
    snapshots = [read_snapshot(repo_path, path) for path in file_paths]
    context, truncated = build_context(snapshots, args.context_limit_chars)
    prompt = build_hardening_prompt(context, truncated)
    llm_output = call_local_llm(prompt)

    generated_at = datetime.now().astimezone()
    report = render_report(
        repo_path=repo_path,
        generated_at=generated_at,
        snapshots=snapshots,
        context=context,
        prompt=prompt,
        llm_output=llm_output,
        truncated=truncated,
    )
    report_path = write_report(report, generated_at)
    print(f"Report written: {report_path}")


if __name__ == "__main__":
    main()
