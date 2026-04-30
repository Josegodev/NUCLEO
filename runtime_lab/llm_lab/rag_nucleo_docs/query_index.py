"""Query the Markdown lexical index with token-overlap scoring."""

from __future__ import annotations

import argparse
import json
import sys

sys.dont_write_bytecode = True

from .build_index import tokenize
from .config import INDEX_FILE


NO_EVIDENCE = "NO_CONSTA_EN_DOCUMENTACION"
DRY_RUN_PHRASE_BOOST = 0.5
DRY_RUN_PHRASES = (
    "does not call tool.run",
    "no llama a tool.run",
    "executed=false",
)


def load_index() -> dict[str, object]:
    """Load the index or fail with a clear error."""
    if not INDEX_FILE.exists():
        raise FileNotFoundError(
            f"Index file not found: {INDEX_FILE}. Run python build_index.py first."
        )
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


def normalize_for_phrase_match(text: str) -> str:
    """Normalize text for exact phrase checks without semantic inference."""
    normalized = text.lower().replace("`", "")
    normalized = " ".join(normalized.split())
    return normalized.replace('"executed": false', "executed=false")


def exact_phrase_boost(question: str, chunk_text: str) -> float:
    """Boost dry_run chunks that contain explicit non-execution evidence."""
    if "dry_run" not in question.lower():
        return 0.0
    normalized_text = normalize_for_phrase_match(chunk_text)
    if any(phrase in normalized_text for phrase in DRY_RUN_PHRASES):
        return DRY_RUN_PHRASE_BOOST
    return 0.0


def score_chunk(
    question: str,
    question_tokens: set[str],
    chunk: dict[str, object],
) -> float:
    """Score one chunk by weighted query-token overlap."""
    if not question_tokens:
        return 0.0
    chunk_tokens = set(str(token) for token in chunk.get("tokens", []))
    overlap = question_tokens & chunk_tokens
    required_overlap = min(2, len(question_tokens))
    if len(overlap) < required_overlap:
        return 0.0
    token_overlap_score = len(overlap) / len(question_tokens)
    source_weight = float(chunk.get("source_weight", 1.0))
    return (token_overlap_score * source_weight) + exact_phrase_boost(
        question,
        str(chunk.get("text", "")),
    )


def query(question: str, top_k: int = 5) -> dict[str, object]:
    """Return top lexical matches for a question."""
    index = load_index()
    question_tokens = set(tokenize(question))
    scored: list[dict[str, object]] = []

    for chunk in index.get("chunks", []):
        if not isinstance(chunk, dict):
            continue
        score = score_chunk(question, question_tokens, chunk)
        if score <= 0:
            continue
        scored.append(
            {
                "score": round(score, 6),
                "chunk_id": str(chunk["chunk_id"]),
                "file": str(chunk["file"]),
                "heading": str(chunk["heading"]),
                "start_line": int(chunk["start_line"]),
                "end_line": int(chunk["end_line"]),
                "text": str(chunk["text"]),
            }
        )

    scored.sort(
        key=lambda item: (
            -float(item["score"]),
            str(item["file"]),
            int(item["start_line"]),
            str(item["chunk_id"]),
        )
    )
    results = scored[:top_k]
    status = "FOUND" if results else NO_EVIDENCE
    return {"question": question, "status": status, "results": results}


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Query the Markdown lexical index.")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    try:
        result = query(args.question, top_k=args.top_k)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
