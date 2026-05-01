"""Compatibility CLI for querying the local Markdown lexical index.

The public retrieval implementation lives in search.py. This module delegates
to it so the result contract cannot drift between two query entrypoints.
"""

from __future__ import annotations

import argparse
import json

try:
    from .config import DEFAULT_TOP_K
    from .search import search
except ImportError:  # pragma: no cover - keeps direct script execution working.
    from config import DEFAULT_TOP_K
    from search import search


def query(question: str, top_k: int = DEFAULT_TOP_K) -> dict[str, object]:
    """Return top matching chunks using the public search() contract."""
    return search(question, top_k=top_k)


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
