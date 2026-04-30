"""Discover Markdown documentation files for lexical retrieval."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from .config import EXCLUDED_PARTS, ROOT, is_included_markdown, relative_to_root


def discover_markdown_files(root: Path = ROOT) -> list[Path]:
    """Return allowed Markdown files under root in deterministic order."""
    files: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        dirnames[:] = sorted(
            dirname for dirname in dirnames if dirname not in EXCLUDED_PARTS
        )
        for filename in sorted(filenames):
            path = current_path / filename
            if is_included_markdown(path):
                files.append(path)
    return sorted(files, key=lambda path: relative_to_root(path).as_posix())


def main() -> None:
    """Print discovered Markdown paths, one per line."""
    for path in discover_markdown_files():
        print(relative_to_root(path).as_posix())


if __name__ == "__main__":
    main()
