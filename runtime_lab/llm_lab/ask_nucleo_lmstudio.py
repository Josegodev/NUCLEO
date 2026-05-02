"""CLI for answering NUCLEO RAG questions through LM Studio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime_lab.llm_lab.lmstudio_rag_adapter import answer_with_lmstudio_rag


EXIT_CODES = {
    "OK": 0,
    "NO_EVIDENCE": 1,
    "LMSTUDIO_UNAVAILABLE": 2,
    "ERROR": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask NUCLEO RAG evidence through LM Studio"
    )
    parser.add_argument("query", help="Question to answer from indexed NUCLEO evidence")
    parser.add_argument("--top-k", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = answer_with_lmstudio_rag(args.query, top_k=args.top_k)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return EXIT_CODES.get(str(result.get("status")), 3)


if __name__ == "__main__":
    sys.exit(main())
