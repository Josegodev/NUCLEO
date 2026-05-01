"""Chunk Markdown files by headings for lexical retrieval.

Chunks preserve source file, heading and line range so answers can cite evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from .config import MAX_CHUNK_CHARS, ROOT
except ImportError:  # pragma: no cover - keeps direct script execution working.
    from config import MAX_CHUNK_CHARS, ROOT


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass(frozen=True)
class MarkdownChunk:
    chunk_id: str
    file: str
    heading: str
    start_line: int
    end_line: int
    text: str


def slugify(value: str) -> str:
    """Create a stable slug for chunk identifiers."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9áéíóúñü]+", "-", value)
    return value.strip("-") or "root"


def split_large_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split oversized text while preserving readability."""
    if len(text) <= max_chars:
        return [text]

    parts: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in text.split("\n\n"):
        paragraph_len = len(paragraph)

        if current and current_len + paragraph_len > max_chars:
            parts.append("\n\n".join(current).strip())
            current = []
            current_len = 0

        current.append(paragraph)
        current_len += paragraph_len + 2

    if current:
        parts.append("\n\n".join(current).strip())

    return [part for part in parts if part]


def chunk_markdown(path: Path, text: str) -> list[MarkdownChunk]:
    """Split a Markdown file into heading-based chunks."""
    relative_file = path.relative_to(ROOT).as_posix()
    lines = text.splitlines()

    sections: list[tuple[str, int, int]] = []
    current_heading = "ROOT"
    current_start = 1

    for idx, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if not match:
            continue

        if idx > current_start:
            sections.append((current_heading, current_start, idx - 1))

        current_heading = match.group(2).strip()
        current_start = idx

    if lines:
        sections.append((current_heading, current_start, len(lines)))

    chunks: list[MarkdownChunk] = []

    for heading, start, end in sections:
        section_text = "\n".join(lines[start - 1:end]).strip()
        if not section_text:
            continue

        parts = split_large_text(section_text)
        for part_index, part in enumerate(parts, start=1):
            suffix = f"-{part_index}" if len(parts) > 1 else ""
            chunk_id = f"{relative_file}#{slugify(heading)}{suffix}"

            chunks.append(
                MarkdownChunk(
                    chunk_id=chunk_id,
                    file=relative_file,
                    heading=heading,
                    start_line=start,
                    end_line=end,
                    text=part,
                )
            )

    return chunks


def chunk_to_dict(chunk: MarkdownChunk) -> dict[str, object]:
    """Serialize a MarkdownChunk to JSON-compatible dict."""
    return asdict(chunk)
