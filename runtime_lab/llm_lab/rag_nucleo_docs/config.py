"""Configuration for the experimental Markdown retrieval lab.

This module is intentionally standalone. It must not import NUCLEO runtime
modules and must not write outside INDEX_DIR.
"""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the NUCLEO repository root from this lab module location."""
    return Path(__file__).resolve().parents[3]


ROOT = repo_root()
INDEX_DIR = Path(__file__).resolve().parent / ".index"
INDEX_FILE = INDEX_DIR / "md_chunks_index.json"
INCLUDED_SUFFIXES = {".md"}
DEFAULT_TOP_K = 5

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "external",
    "node_modules",
    "outputs",
    "llm_context",
    "CONTROL_OPERATIVO",
}
EXCLUDED_PREFIXES = {
    Path("docs_esp/_deprecated"),
    Path("runtime_lab/llm_lab/rag_nucleo_docs"),
    Path("runtime_lab/llm_lab/reports"),
}


def relative_to_root(path: Path) -> Path:
    """Return a path relative to ROOT."""
    return path.resolve().relative_to(ROOT)


def is_excluded(path: Path) -> bool:
    """Return True when a path is outside the allowed documentation scope."""
    relative_path = relative_to_root(path)
    if any(part in EXCLUDED_PARTS for part in relative_path.parts):
        return True
    return any(
        relative_path == prefix or relative_path.is_relative_to(prefix)
        for prefix in EXCLUDED_PREFIXES
    )


def is_included_markdown(path: Path) -> bool:
    """Return True when path is an allowed Markdown source file."""
    return path.is_file() and path.suffix in INCLUDED_SUFFIXES and not is_excluded(path)
