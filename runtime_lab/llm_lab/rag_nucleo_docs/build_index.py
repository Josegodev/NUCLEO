"""Build a deterministic lexical index over allowed Markdown documentation."""

from __future__ import annotations

import json
import re
import sys
import unicodedata

sys.dont_write_bytecode = True

from .chunk_md import chunk_markdown_file
from .config import INDEX_DIR, INDEX_FILE, relative_to_root, source_profile
from .ingest_md import discover_markdown_files


TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_]+")
NORMALIZED_TOKEN_RE = re.compile(r"[a-z0-9_]+")
STOPWORDS = {
    "a",
    "al",
    "and",
    "campos",
    "cual",
    "cuál",
    "de",
    "del",
    "el",
    "en",
    "es",
    "for",
    "hace",
    "in",
    "la",
    "las",
    "los",
    "of",
    "on",
    "or",
    "para",
    "por",
    "que",
    "qué",
    "the",
    "tener",
    "tiene",
    "to",
    "un",
    "una",
    "valores",
    "puede",
    "y",
}


def tokenize(text: str) -> list[str]:
    """Tokenize text with a simple deterministic regex."""
    return sorted(
        set(
            token.lower()
            for token in TOKEN_RE.findall(text)
            if token.lower() not in STOPWORDS
        )
    )


def normalize_text(text: str) -> str:
    """Normalize text for accent-insensitive lexical retrieval."""
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(char)
    )
    without_symbols = re.sub(r"[^a-z0-9_]+", " ", without_accents)
    return " ".join(without_symbols.split())


def normalized_tokenize(text: str) -> list[str]:
    """Tokenize normalized text deterministically."""
    normalized = normalize_text(text)
    return sorted(
        set(
            token
            for token in NORMALIZED_TOKEN_RE.findall(normalized)
            if token not in STOPWORDS
        )
    )


def build_index() -> dict[str, object]:
    """Build the Markdown chunk index without copying source files elsewhere."""
    chunks: list[dict[str, object]] = []
    for path in discover_markdown_files():
        for chunk in chunk_markdown_file(path):
            indexed_chunk = dict(chunk)
            source_type, source_weight = source_profile(str(chunk["file"]))
            indexed_chunk["source_type"] = source_type
            indexed_chunk["source_weight"] = source_weight
            indexed_chunk["tokens"] = tokenize(str(chunk["text"]))
            indexed_chunk["normalized_text"] = normalize_text(str(chunk["text"]))
            indexed_chunk["normalized_tokens"] = normalized_tokenize(str(chunk["text"]))
            chunks.append(indexed_chunk)

    chunks.sort(key=lambda item: (str(item["file"]), int(item["start_line"]), str(item["chunk_id"])))
    return {"chunks": chunks}


def write_index(index: dict[str, object]) -> None:
    """Write the index inside the module-owned .index directory."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Build and write the Markdown lexical index."""
    index = build_index()
    write_index(index)
    print(f"Wrote {relative_to_root(INDEX_FILE).as_posix()}")
    print(f"Chunks indexed: {len(index['chunks'])}")


if __name__ == "__main__":
    main()
