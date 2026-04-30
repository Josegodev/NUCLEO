"""Generate evidence-bound answers from retrieved Markdown chunks.

First HARDENING-safe version:
- no LLM
- no runtime imports
- no tool execution
- extractive answer only
"""

from __future__ import annotations

import argparse
import json

from .config import DEFAULT_TOP_K
from .query_index import query


def build_answer(question: str, top_k: int = DEFAULT_TOP_K) -> dict[str, object]:
    """Build an evidence-bound answer from lexical retrieval."""
    retrieval = query(question, top_k=top_k)

    if retrieval["status"] != "FOUND":
        return {
            "question": question,
            "answer": "NO_CONSTA_EN_DOCUMENTACION",
            "sources": [],
            "warnings": [
                "No matching Markdown evidence was found in the indexed documentation."
            ],
        }

    sources = []
    evidence_lines = []

    for result in retrieval["results"]:
        sources.append(
            {
                "file": result["file"],
                "heading": result["heading"],
                "start_line": result["start_line"],
                "end_line": result["end_line"],
                "score": result["score"],
            }
        )

        snippet = str(result["text"]).strip()
        if len(snippet) > 700:
            snippet = snippet[:700].rstrip() + "..."

        evidence_lines.append(
            f"[{result['file']}:{result['start_line']}-{result['end_line']}]\n"
            f"{snippet}"
        )

    return {
        "question": question,
        "answer": "\n\n".join(evidence_lines),
        "sources": sources,
        "warnings": [
            "Extractive answer only. No LLM synthesis has been applied."
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Answer using NUCLEO Markdown evidence")
    parser.add_argument("question", help="Question to answer from documentation")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_answer(args.question, top_k=args.top_k)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
