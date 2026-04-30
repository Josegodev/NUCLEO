"""Chunk Markdown files by level 1-3 headings."""

from __future__ import annotations

import re
from pathlib import Path

from .config import ROOT, relative_to_root


HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
SLUG_RE = re.compile(r"[^a-z0-9]+")


def heading_slug(heading: str) -> str:
    """Return a stable slug for a Markdown heading."""
    normalized = heading.strip().lower()
    normalized = SLUG_RE.sub("-", normalized)
    return normalized.strip("-") or "document"


def chunk_id(file_path: str, heading: str, seen: dict[str, int]) -> str:
    """Return a stable chunk id based on file and heading."""
    base_id = f"{file_path}#{heading_slug(heading)}"
    seen[base_id] = seen.get(base_id, 0) + 1
    if seen[base_id] == 1:
        return base_id
    return f"{base_id}-{seen[base_id]}"


def chunk_markdown_file(path: Path, root: Path = ROOT) -> list[dict[str, object]]:
    """Split one Markdown file into heading-based chunks."""
    relative_file = relative_to_root(path).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    headings: list[tuple[int, str]] = []

    for line_number, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            headings.append((line_number, match.group(2).strip()))

    if not headings:
        headings = [(1, Path(relative_file).stem)]

    chunks: list[dict[str, object]] = []
    seen_ids: dict[str, int] = {}

    for index, (start_line, heading) in enumerate(headings):
        next_start = headings[index + 1][0] if index + 1 < len(headings) else len(lines) + 1
        end_line = max(start_line, next_start - 1)
        text = "\n".join(lines[start_line - 1:end_line]).strip()
        if not text:
            continue
        chunks.append(
            {
                "chunk_id": chunk_id(relative_file, heading, seen_ids),
                "file": relative_file,
                "heading": heading,
                "start_line": start_line,
                "end_line": end_line,
                "text": text,
            }
        )

    return chunks
