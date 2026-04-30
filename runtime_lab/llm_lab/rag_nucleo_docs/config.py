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
SOURCE_WEIGHTS = {
    "docs/modules/code_contracts.md": 2.0,
    "docs/modules/": 1.6,
    "docs/architecture.md": 1.5,
    "docs/operations/": 1.2,
    "README.md": 0.9,
    "docs/vision/": 0.7,
    "docs/planning/": 0.7,
}
DEFAULT_SOURCE_WEIGHT = 1.0
QUERY_SYNONYMS = {
    "dry_run": ["dryrun", "dry-run"],
    "execute": ["run", "call", "invoke"],
    "tool": ["tool", "herramienta"],
}

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


def source_profile(relative_file: str) -> tuple[str, float]:
    """Return source type and weight for a repository-relative Markdown file."""
    if relative_file == "docs/modules/code_contracts.md":
        return "code_contracts", SOURCE_WEIGHTS["docs/modules/code_contracts.md"]
    if relative_file.startswith("docs/modules/"):
        return "module_docs", SOURCE_WEIGHTS["docs/modules/"]
    if relative_file == "docs/architecture.md":
        return "architecture", SOURCE_WEIGHTS["docs/architecture.md"]
    if relative_file.startswith("docs/operations/"):
        return "operations", SOURCE_WEIGHTS["docs/operations/"]
    if relative_file == "README.md":
        return "readme", SOURCE_WEIGHTS["README.md"]
    if relative_file.startswith("docs/vision/"):
        return "vision", SOURCE_WEIGHTS["docs/vision/"]
    if relative_file.startswith("docs/planning/"):
        return "planning", SOURCE_WEIGHTS["docs/planning/"]
    return "other", DEFAULT_SOURCE_WEIGHT
