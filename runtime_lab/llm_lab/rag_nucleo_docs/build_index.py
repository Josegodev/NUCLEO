"""Build a local lexical index from live NUCLEO Markdown documentation.

This index stores chunks and lightweight lexical tokens. It does not store
copied source documents as authoritative data; it is only a cache.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

try:
    from .chunk_md import chunk_markdown, chunk_to_dict
    from .config import INDEX_DIR, INDEX_FILE, ROOT
    from .ingest_md import discover_markdown_files, read_markdown
except ImportError:  # pragma: no cover - keeps direct script execution working.
    from chunk_md import chunk_markdown, chunk_to_dict
    from config import INDEX_DIR, INDEX_FILE, ROOT
    from ingest_md import discover_markdown_files, read_markdown


TOKEN_RE = re.compile(r"[a-zA-Z0-9_áéíóúÁÉÍÓÚñÑüÜ]+")


def tokenize(text: str) -> list[str]:
    """Normalize text into lexical tokens."""
    return [token.lower() for token in TOKEN_RE.findall(text)]


def normalize_text(text: str) -> str:
    """Return deterministic normalized text for retrieval checks."""
    return " ".join(tokenize(text))


def build_index() -> dict[str, object]:
    """Build the Markdown chunk index."""
    files = discover_markdown_files()
    chunks: list[dict[str, object]] = []

    for path in files:
        text = read_markdown(path)
        for chunk in chunk_markdown(path, text):
            item = chunk_to_dict(chunk)
            item["tokens"] = sorted(set(tokenize(chunk.text)))
            chunks.append(item)

    return {
        "project": "NUCLEO",
        "index_type": "lexical_markdown_chunks",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_root": ROOT.as_posix(),
        "files_indexed": len(files),
        "chunks_indexed": len(chunks),
        "chunks": chunks,
    }


def write_index(index: dict[str, object]) -> None:
    """Write index atomically enough for local lab use."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    index = build_index()
    write_index(index)

    print(f"Wrote {INDEX_FILE.relative_to(ROOT)}")
    print(f"Files indexed: {index['files_indexed']}")
    print(f"Chunks indexed: {index['chunks_indexed']}")


if __name__ == "__main__":
    main()
