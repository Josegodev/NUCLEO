"""Discover live Markdown files for NUCLEO documentation retrieval.

This script only reads Markdown files. It does not copy source documents and
does not import runtime components.
"""

from __future__ import annotations

from pathlib import Path

try:
    from .config import INCLUDED_SUFFIXES, ROOT, is_excluded
except ImportError:  # pragma: no cover - keeps direct script execution working.
    from config import INCLUDED_SUFFIXES, ROOT, is_excluded


def discover_markdown_files(root: Path = ROOT) -> list[Path]:
    """Return Markdown files eligible for indexing."""
    files: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in INCLUDED_SUFFIXES:
            continue

        if is_excluded(path):
            continue

        files.append(path)

    return sorted(files)


def read_markdown(path: Path) -> str:
    """Read Markdown as UTF-8 text with replacement for invalid bytes."""
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    files = discover_markdown_files()
    for path in files:
        print(path.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
