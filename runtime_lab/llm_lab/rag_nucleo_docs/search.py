"""Public deterministic lexical search API for rag_nucleo_docs."""

from __future__ import annotations

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


def build_result(chunk: dict[str, object], score: float) -> dict[str, object]:
    """Build a stable public result while keeping legacy fields available."""
    text = str(chunk["text"])
    doc_id = str(chunk["chunk_id"])
    return {
        "doc_id": doc_id,
        "score": round(score, 6),
        "snippet": text,
        "chunk_id": doc_id,
        "file": str(chunk["file"]),
        "heading": str(chunk["heading"]),
        "start_line": int(chunk["start_line"]),
        "end_line": int(chunk["end_line"]),
        "text": text,
    }


def search(query: str, top_k: int = 5) -> dict[str, object]:
    """Return deterministic lexical matches for a query."""
    if top_k < 0:
        raise ValueError("top_k must be greater than or equal to 0")

    index = load_index()
    base_query_tokens = set(normalized_tokenize(query))
    query_tokens = expand_query_tokens(base_query_tokens)
    scored: list[dict[str, object]] = []

    for chunk in index.get("chunks", []):
        if not isinstance(chunk, dict):
            continue
        score = score_chunk(query, query_tokens, len(base_query_tokens), chunk)
        if score <= 0:
            continue
        scored.append(build_result(chunk, score))

    scored.sort(
        key=lambda item: (
            -float(item["score"]),
            str(item["file"]),
            int(item["start_line"]),
            str(item["doc_id"]),
        )
    )
    results = scored[:top_k]
    status = "FOUND" if results else NO_EVIDENCE
    return {
        "query": query,
        "question": query,
        "status": status,
        "results": results,
    }
