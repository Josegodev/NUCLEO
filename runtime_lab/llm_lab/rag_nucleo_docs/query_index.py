"""Legacy CLI wrapper for the public search API.

All retrieval logic lives in search.py. This module remains temporarily so
existing callers of query_index.py keep working during the migration.
"""

from __future__ import annotations

import argparse
import json
import sys

sys.dont_write_bytecode = True

from .search import search


def query(question: str, top_k: int = 5) -> dict[str, object]:
    """Legacy compatibility wrapper around search()."""
    return search(question, top_k=top_k)


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Legacy wrapper around rag_nucleo_docs.search."
    )
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    try:
        result = search(args.question, top_k=args.top_k)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
