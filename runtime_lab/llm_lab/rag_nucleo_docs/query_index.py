"""Query the Markdown lexical index with token-overlap scoring."""

from __future__ import annotations

import argparse
import json
import sys

sys.dont_write_bytecode = True

from .build_index import normalize_text, normalized_tokenize
from .config import INDEX_FILE, QUERY_SYNONYMS


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
    return normalize_text(text)


def exact_phrase_boost(question: str, chunk_text: str) -> float:
    """Boost dry_run chunks that contain explicit non-execution evidence."""
    expanded_question_tokens = expand_query_tokens(set(normalized_tokenize(question)))
    if "dry_run" not in expanded_question_tokens:
        return 0.0
    normalized_text = normalize_for_phrase_match(chunk_text)
    normalized_phrases = [normalize_text(phrase) for phrase in DRY_RUN_PHRASES]
    if any(phrase in normalized_text for phrase in normalized_phrases):
        return DRY_RUN_PHRASE_BOOST
    return 0.0


def expand_query_tokens(tokens: set[str]) -> set[str]:
    """Expand query tokens with deterministic manual synonyms."""
    expanded = set(tokens)
    for term, synonyms in QUERY_SYNONYMS.items():
        term_tokens = set(normalized_tokenize(term))
        synonym_token_sets = [
            set(normalized_tokenize(synonym)) for synonym in synonyms
        ]

        term_matched = bool(expanded & term_tokens)
        synonym_matched = any(
            synonym_tokens and synonym_tokens <= expanded
            for synonym_tokens in synonym_token_sets
        )
        if term_matched or synonym_matched:
            expanded.update(term_tokens)
            for synonym_tokens in synonym_token_sets:
                expanded.update(synonym_tokens)

    return expanded


def score_chunk(
    question: str,
    question_tokens: set[str],
    base_question_token_count: int,
    chunk: dict[str, object],
) -> float:
    """Score one chunk by weighted query-token overlap."""
    if not question_tokens:
        return 0.0
    chunk_tokens = set(str(token) for token in chunk.get("normalized_tokens", []))
    overlap = question_tokens & chunk_tokens
    required_overlap = min(2, max(base_question_token_count, 1))
    if len(overlap) < required_overlap:
        return 0.0
    token_overlap_score = min(1.0, len(overlap) / max(base_question_token_count, 1))
    source_weight = float(chunk.get("source_weight", 1.0))
    return (token_overlap_score * source_weight) + exact_phrase_boost(
        question,
        str(chunk.get("text", "")),
    )


def query(question: str, top_k: int = 5) -> dict[str, object]:
    """Return top lexical matches for a question."""
    index = load_index()
    base_question_tokens = set(normalized_tokenize(question))
    question_tokens = expand_query_tokens(base_question_tokens)
    scored: list[dict[str, object]] = []

    for chunk in index.get("chunks", []):
        if not isinstance(chunk, dict):
            continue
        score = score_chunk(question, question_tokens, len(base_question_tokens), chunk)
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
