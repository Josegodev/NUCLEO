"""Build local LLM context Markdown from document_loader JSONL.

This script is runtime_lab-only infrastructure. It does not call local models,
does not call network services, and does not import NUCLEO runtime modules.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_NAME = "NUCLEO"
PROJECT_PHASE = "HARDENING"
NO_PARSER_STATUS = "no parser integrated"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build deterministic local LLM context Markdown from JSONL.",
    )
    parser.add_argument(
        "jsonl_path",
        type=Path,
        help="Path to a document_loader JSONL file.",
    )
    parser.add_argument(
        "--output-context-md",
        type=Path,
        default=None,
        help="Optional output path for the generated context Markdown.",
    )
    return parser.parse_args()


def read_jsonl(jsonl_path: Path) -> list[dict[str, Any]]:
    if not jsonl_path.exists():
        raise ValueError(f"JSONL file does not exist: {jsonl_path}")

    if not jsonl_path.is_file():
        raise ValueError(f"JSONL path is not a file: {jsonl_path}")

    records: list[dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSONL at line {line_number}: {exc.msg}"
                ) from exc

            if not isinstance(record, dict):
                raise ValueError(f"JSONL line {line_number} is not an object")

            records.append(record)

    return records


def infer_document_id(jsonl_path: Path, records: list[dict[str, Any]]) -> str:
    if records:
        document_id = records[0].get("document_id")
        if isinstance(document_id, str) and document_id:
            return document_id

    return jsonl_path.stem


def default_context_path(jsonl_path: Path, document_id: str) -> Path:
    resolved_jsonl = jsonl_path.resolve()
    if resolved_jsonl.parent.name == "documents":
        return resolved_jsonl.parent.parent / "llm_context" / f"{document_id}.context.md"

    return resolved_jsonl.with_suffix(".context.md")


def default_manifest_path(jsonl_path: Path, document_id: str) -> Path:
    resolved_jsonl = jsonl_path.resolve()
    if resolved_jsonl.parent.name == "documents":
        return resolved_jsonl.parent.parent / "manifests" / f"{document_id}.manifest.json"

    return resolved_jsonl.with_suffix(".manifest.json")


def read_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        return {}

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    if not isinstance(manifest, dict):
        raise ValueError(f"manifest is not an object: {manifest_path}")

    return manifest


def build_context_markdown(
    *,
    document_id: str,
    records: list[dict[str, Any]],
    parser_status: str,
    records_written: int,
    source_path: str | None = None,
) -> str:
    lines = [
        "# Local LLM Context",
        "",
        f"Project: {PROJECT_NAME}",
        f"Phase: {PROJECT_PHASE}",
        f"Source document_id: {document_id}",
        f"Parser status: {parser_status}",
        f"Records written: {records_written}",
    ]

    if source_path:
        lines.append(f"Source path: {source_path}")

    lines.extend(["", "Content:"])

    if not records:
        if parser_status == NO_PARSER_STATUS:
            lines.append("No parser integrated yet.")
        else:
            lines.append("No extracted content records found.")
        return "\n".join(lines) + "\n"

    for index, record in enumerate(records, start=1):
        content = record.get("content")
        if not isinstance(content, str):
            raise ValueError(f"record {index} is missing string field: content")

        lines.extend(
            [
                "",
                f"## Block {index}",
                f"Page: {record.get('page', '')}",
                f"Block type: {record.get('block_type', '')}",
                f"Content hash: {record.get('content_hash', '')}",
                "",
                content,
            ]
        )

    return "\n".join(lines) + "\n"


def write_text_file(output_path: Path, content: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temp_path.write_text(content, encoding="utf-8", newline="\n")
    temp_path.replace(output_path)


def main() -> int:
    args = parse_args()
    jsonl_path = args.jsonl_path.resolve()

    try:
        records = read_jsonl(jsonl_path)
        document_id = infer_document_id(jsonl_path, records)
        manifest = read_manifest(default_manifest_path(jsonl_path, document_id))
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc

    parser_status = str(manifest.get("parser_status", "unknown"))
    source_path = manifest.get("source_path")
    if not isinstance(source_path, str):
        source_path = None

    output_context_md = (
        args.output_context_md.resolve()
        if args.output_context_md
        else default_context_path(jsonl_path, document_id)
    )
    context_markdown = build_context_markdown(
        document_id=document_id,
        records=records,
        parser_status=parser_status,
        records_written=len(records),
        source_path=source_path,
    )
    write_text_file(output_context_md, context_markdown)

    print(f"input_jsonl: {jsonl_path}")
    print(f"output_context_md: {output_context_md}")
    print(f"document_id: {document_id}")
    print(f"records_written: {len(records)}")
    print("llm_calls: 0")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
