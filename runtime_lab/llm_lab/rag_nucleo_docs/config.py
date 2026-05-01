"""Configuration for NUCLEO Markdown RAG experiments.

This module defines read-only paths and exclusion rules for indexing live
NUCLEO Markdown documentation from llm_lab.

It must not import or call NUCLEO runtime components.
"""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the NUCLEO repository root.

    Expected location:
    runtime_lab/llm_lab/rag_nucleo_docs/config.py
    """
    return Path(__file__).resolve().parents[3]


ROOT = repo_root()

INDEX_DIR = ROOT / "runtime_lab" / "llm_lab" / "rag_nucleo_docs" / ".index"
INDEX_FILE = INDEX_DIR / "md_chunks_index.json"

INCLUDED_SUFFIXES = {".md"}

EXCLUDED_DIR_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "outputs",
    "llm_context",
    "CONTROL_OPERATIVO",
}

EXCLUDED_PATH_PARTS = {
    "docs_esp/_deprecated",
    "runtime_lab/llm_lab/reports",
}

DEFAULT_TOP_K = 5
MAX_CHUNK_CHARS = 6000


def is_excluded(path: Path) -> bool:
    """Return True when path must not be indexed."""
    relative = path.relative_to(ROOT).as_posix()

    if any(part in path.parts for part in EXCLUDED_DIR_PARTS):
        return True

    if any(excluded in relative for excluded in EXCLUDED_PATH_PARTS):
        return True

    return False