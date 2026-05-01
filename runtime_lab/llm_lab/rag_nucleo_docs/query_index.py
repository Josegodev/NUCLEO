"""Query the local NUCLEO Markdown lexical index.

This is retrieval only. It does not call an LLM and does not execute NUCLEO tools.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from config import DEFAULT_TOP_K, INDEX_FILE


TOKEN_RE = re.compile(r"[a-zA-Z0-9_áéíóúÁÉÍÓÚñÑüÜ]+")


def tokenize(text: str) -> set[str]:
    """Normalize query into lexical tokens."""
    return {token.lower() for token in TOKEN_RE.findall(text)}


def load_index(path: Path = INDEX_FILE) -> dict[str, object]:
    """Load existing lexical index."""
    if not path.exists():
        raise FileNotFoundError(
            f"Index not found: {path}. Run build_index.py first."
        )

    return json.loads(path.read_text(encoding="utf-8"))


def score_chunk(query_tokens: set[str], chunk: dict[str, object]) -> float:
    """Score chunk by token overlap."""
    chunk_tokens = set(chunk.get("tokens", []))
    if not query_tokens or not chunk_tokens:
        return 0.0

    overlap = query_tokens & chunk_tokens
    return len(overlap) / len(query_tokens)


def query(question: str, top_k: int = DEFAULT_TOP_K) -> dict[str, object]:
    """Return top matching chunks for a question."""
    index = load_index()
    query_tokens = tokenize(question)

    scored: list[dict[str, object]] = []
    for chunk in index.get("chunks", []):
        if not isinstance(chunk, dict):
            continue

        score = score_chunk(query_tokens, chunk)
        if score <= 0:
            continue

        scored.append(
            {
                "score": round(score, 4),
                "chunk_id": chunk["chunk_id"],
                "file": chunk["file"],
                "heading": chunk["heading"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "text": chunk["text"],
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)

    if not scored:
        return {
            "question": question,
            "status": "NO_CONSTA_EN_DOCUMENTACION",
            "results": [],
        }

    return {
        "question": question,
        "status": "FOUND",
        "results": scored[:top_k],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query NUCLEO Markdown index")
    parser.add_argument("question", help="Question to search in documentation")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = query(args.question, top_k=args.top_k)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()