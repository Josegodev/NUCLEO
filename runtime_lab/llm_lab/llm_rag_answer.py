"""LLM-powered RAG answer layer for experimental llm_lab.

This module consumes deterministic evidence from rag_nucleo_docs and generates
answers using LLM models via model_adapter. It belongs to runtime_lab/llm_lab
and does not integrate with NUCLEO runtime.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from runtime_lab.llm_lab.model_adapter import call_model
from runtime_lab.llm_lab.rag_nucleo_docs.evidence import (
    EVIDENCE_FOUND,
    NO_EVIDENCE,
    build_evidence_package,
)


def build_llm_rag_answer(
    query: str,
    model_id: str,
    top_k: int = 3,
    mode: str = "ollama",
    timeout_ms: int = 30000,
) -> dict[str, Any]:
    """Build an LLM-powered answer from deterministic evidence."""
    evidence_package = build_evidence_package(query, top_k=top_k)
    status = evidence_package.get("status")
    evidence = evidence_package.get("evidence", [])

    if status == NO_EVIDENCE:
        answer = "NO_CONSTA_EN_DOCUMENTACION"
    elif status == EVIDENCE_FOUND:
        # Build prompt from snippets
        snippets = [
            str(item.get("snippet", "")).strip()
            for item in evidence
            if isinstance(item, dict) and str(item.get("snippet", "")).strip()
        ]
        prompt = f"""Responde la pregunta basada únicamente en los siguientes snippets de documentación:

{"\n\n".join(snippets)}

Pregunta: {query}

Respuesta:"""

        # Call the model
        model_call = call_model(model_id, prompt, mode=mode, timeout_ms=timeout_ms)
        if model_call.status == "success":
            answer = model_call.output
        else:
            answer = f"Error en la llamada al modelo: {model_call.error_message}"
    else:
        raise ValueError(f"Estado de evidencia no soportado: {status}")

    return {
        "query": query,
        "model": model_id,
        "status": status,
        "answer": answer,
        "evidence": evidence,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Answer questions using LLM-powered RAG from NUCLEO documentation"
    )
    parser.add_argument("query", help="Question to answer")
    parser.add_argument("--model", default="mistral", help="Model ID to use (default: mistral)")
    parser.add_argument("--top-k", type=int, default=3, help="Number of top evidence snippets (default: 3)")
    parser.add_argument("--mode", default="ollama", help="Adapter mode (default: ollama)")
    parser.add_argument("--timeout-ms", type=int, default=30000, help="Timeout in ms (default: 30000)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_llm_rag_answer(
        query=args.query,
        model_id=args.model,
        top_k=args.top_k,
        mode=args.mode,
        timeout_ms=args.timeout_ms,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()