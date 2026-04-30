"""Generate evidence-bound answers from retrieved Markdown chunks.

This module belongs to runtime_lab/llm_lab. It does not import or call NUCLEO
runtime components, and it never executes tools.
"""

from __future__ import annotations

import argparse
import json

from .config import DEFAULT_TOP_K
from .query_index import query
from ..model_adapter import AdapterMode, call_model


NO_EVIDENCE = "NO_CONSTA_EN_DOCUMENTACION"
DEFAULT_MODEL_ID = "qwen"
DEFAULT_ADAPTER_MODE: AdapterMode = "ollama"
DEFAULT_TIMEOUT_MS = 120000


def build_prompt(question: str, retrieved_chunks: list[dict[str, object]]) -> str:
    """Build the bounded model prompt from full retrieved chunks."""
    chunks = []
    for chunk in retrieved_chunks:
        chunks.append(
            "\n".join(
                [
                    f"Source: {chunk['file']}:{chunk['start_line']}-{chunk['end_line']}",
                    f"Heading: {chunk['heading']}",
                    "Text:",
                    str(chunk["text"]),
                ]
            )
        )

    return (
        "You are reviewing NUCLEO documentation.\n\n"
        "Answer ONLY using the provided context.\n"
        "Do NOT invent information.\n\n"
        "If the answer is not explicitly supported:\n"
        "respond EXACTLY with:\n"
        "NO_CONSTA_EN_DOCUMENTACION\n\n"
        "Question:\n"
        f"{question}\n\n"
        "Context:\n"
        f"{'\n\n---\n\n'.join(chunks)}\n"
    )


def build_sources(results: list[dict[str, object]]) -> list[dict[str, object]]:
    """Build the stable source list for both answer modes."""
    return [
        {
            "file": result["file"],
            "heading": result["heading"],
            "start_line": result["start_line"],
            "end_line": result["end_line"],
            "score": result["score"],
        }
        for result in results
    ]


def build_extractive_answer(
    question: str,
    results: list[dict[str, object]],
) -> dict[str, object]:
    """Build an extractive answer from retrieved chunks."""
    sources = build_sources(results)
    evidence_lines = []

    for result in results:
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


def build_llm_answer(
    question: str,
    results: list[dict[str, object]],
    *,
    model_id: str = DEFAULT_MODEL_ID,
    adapter_mode: AdapterMode = DEFAULT_ADAPTER_MODE,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> dict[str, object]:
    """Build a model-synthesized answer constrained by retrieved evidence."""
    prompt = build_prompt(question, results)
    model_result = call_model(
        model_id,
        prompt,
        mode=adapter_mode,
        timeout_ms=timeout_ms,
    )
    sources = build_sources(results)
    warnings = [
        "LLM mode used runtime_lab/llm_lab model_adapter only.",
        "The prompt instructs the model to answer only from retrieved context.",
    ]

    if model_result.status != "success":
        error_type = model_result.error_type or "llm_synthesis_failed"
        if error_type == "model_not_available":
            warnings.append("model_not_available")
        else:
            warnings.append("llm_synthesis_failed")
            warnings.append(f"model_error_type={error_type}")
        fallback = build_extractive_answer(question, results)
        fallback["warnings"] = warnings + [
            "Returned extractive evidence instead of LLM synthesis."
        ]
        return fallback

    answer = (model_result.output or "").strip()
    if not answer or answer == NO_EVIDENCE:
        fallback = build_extractive_answer(question, results)
        fallback["warnings"] = warnings + [
            "llm_returned_no_consta_despite_retrieved_evidence",
            "Returned extractive evidence instead of LLM synthesis.",
        ]
        return fallback

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "warnings": warnings,
    }


def build_answer(
    question: str,
    top_k: int = DEFAULT_TOP_K,
    mode: str = "extractive",
    model_id: str = DEFAULT_MODEL_ID,
    adapter_mode: AdapterMode = DEFAULT_ADAPTER_MODE,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> dict[str, object]:
    """Build an evidence-bound answer from lexical retrieval."""
    retrieval = query(question, top_k=top_k)

    if retrieval["status"] != "FOUND":
        return {
            "question": question,
            "answer": NO_EVIDENCE,
            "sources": [],
            "warnings": [
                "No matching Markdown evidence was found in the indexed documentation."
            ],
        }

    results = list(retrieval["results"])
    if mode == "extractive":
        return build_extractive_answer(question, results)

    return build_llm_answer(
        question,
        results,
        model_id=model_id,
        adapter_mode=adapter_mode,
        timeout_ms=timeout_ms,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Answer using NUCLEO Markdown evidence")
    parser.add_argument("question", help="Question to answer from documentation")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--mode", choices=["extractive", "llm"], default="extractive")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument(
        "--adapter-mode",
        choices=["ollama", "mock_success", "mock_errors"],
        default=DEFAULT_ADAPTER_MODE,
    )
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_answer(
        args.question,
        top_k=args.top_k,
        mode=args.mode,
        model_id=args.model_id,
        adapter_mode=args.adapter_mode,
        timeout_ms=args.timeout_ms,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
