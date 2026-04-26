"""Validate document_loader JSONL records against the parser contract.

This script is intentionally local to runtime_lab. It does not import NUCLEO
runtime modules and does not call any parser, model, or network service.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from loader_config import MAX_CONTENT_CHARS_PER_RECORD
from loader_config import MAX_PAGES
from loader_config import MAX_RECORDS_PER_DOCUMENT
from loader_config import MAX_TOTAL_CONTENT_CHARS


ALLOWED_BLOCK_TYPES = {"text", "table", "image", "metadata"}
ALLOWED_PARSER_STATUSES = {
    "no parser integrated",
    "parsed",
    "parser_error",
    "input_error",
}
NO_PARSER_STATUS = "no parser integrated"
REQUIRED_FIELDS = {
    "document_id",
    "source_path",
    "page",
    "block_type",
    "content",
    "content_hash",
    "created_at",
}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate document_loader JSONL records.",
    )
    parser.add_argument(
        "jsonl_path",
        type=Path,
        help="Path to the document_loader JSONL file.",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="Optional manifest path. Defaults to the sibling knowledge_store manifest.",
    )
    return parser.parse_args()


def default_manifest_path(jsonl_path: Path, document_id: str | None = None) -> Path:
    resolved_jsonl = jsonl_path.resolve()
    inferred_document_id = document_id or resolved_jsonl.stem

    if resolved_jsonl.parent.name == "documents":
        return (
            resolved_jsonl.parent.parent
            / "manifests"
            / f"{inferred_document_id}.manifest.json"
        )

    return resolved_jsonl.with_suffix(".manifest.json")


def read_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        return {}

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    if not isinstance(manifest, dict):
        raise ValueError(f"manifest is not a JSON object: {manifest_path}")

    return manifest


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
                    f"line {line_number}: invalid JSON: {exc.msg}"
                ) from exc

            if not isinstance(record, dict):
                raise ValueError(f"line {line_number}: record must be a JSON object")

            records.append(record)

    return records


def validate_records_for_contract(
    *,
    records: list[dict[str, Any]],
    jsonl_path: Path,
    manifest: dict[str, Any],
) -> None:
    for line_number, record in enumerate(records, start=1):
        validate_record(record, line_number)

    validate_consistency(
        records=records,
        jsonl_path=jsonl_path,
        manifest=manifest,
    )


def validate_record(record: dict[str, Any], line_number: int) -> None:
    missing_fields = sorted(REQUIRED_FIELDS - set(record))
    if missing_fields:
        raise ValueError(
            f"line {line_number}: missing required fields: {', '.join(missing_fields)}"
        )

    document_id = record["document_id"]
    if not isinstance(document_id, str) or not SHA256_PATTERN.fullmatch(document_id):
        raise ValueError(f"line {line_number}: document_id must be lowercase SHA256")

    source_path = record["source_path"]
    if not isinstance(source_path, str) or not source_path:
        raise ValueError(f"line {line_number}: source_path must be a non-empty string")

    page = record["page"]
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError(f"line {line_number}: page must be an integer >= 1")

    if page > MAX_PAGES:
        raise ValueError(
            f"line {line_number}: page exceeds MAX_PAGES: {page} > {MAX_PAGES}"
        )

    block_type = record["block_type"]
    if block_type not in ALLOWED_BLOCK_TYPES:
        allowed = ", ".join(sorted(ALLOWED_BLOCK_TYPES))
        raise ValueError(
            f"line {line_number}: block_type must be one of: {allowed}"
        )

    content = record["content"]
    if not isinstance(content, str):
        raise ValueError(f"line {line_number}: content must be a string")

    if len(content) > MAX_CONTENT_CHARS_PER_RECORD:
        raise ValueError(
            f"line {line_number}: content length exceeds "
            f"MAX_CONTENT_CHARS_PER_RECORD: "
            f"{len(content)} > {MAX_CONTENT_CHARS_PER_RECORD}"
        )

    content_hash = record["content_hash"]
    if not isinstance(content_hash, str) or not SHA256_PATTERN.fullmatch(content_hash):
        raise ValueError(f"line {line_number}: content_hash must be lowercase SHA256")

    expected_hash = sha256_text(content)
    if content_hash != expected_hash:
        raise ValueError(f"line {line_number}: content_hash does not match content")

    created_at = record["created_at"]
    if not isinstance(created_at, str) or not created_at:
        raise ValueError(f"line {line_number}: created_at must be a non-empty string")


def validate_consistency(
    *,
    records: list[dict[str, Any]],
    jsonl_path: Path,
    manifest: dict[str, Any],
) -> None:
    parser_status = manifest.get("parser_status")

    if len(records) > MAX_RECORDS_PER_DOCUMENT:
        raise ValueError(
            "record count exceeds MAX_RECORDS_PER_DOCUMENT: "
            f"{len(records)} > {MAX_RECORDS_PER_DOCUMENT}"
        )

    total_content_chars = sum(len(record.get("content", "")) for record in records)
    if total_content_chars > MAX_TOTAL_CONTENT_CHARS:
        raise ValueError(
            "total content length exceeds MAX_TOTAL_CONTENT_CHARS: "
            f"{total_content_chars} > {MAX_TOTAL_CONTENT_CHARS}"
        )

    if parser_status is not None and parser_status not in ALLOWED_PARSER_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_PARSER_STATUSES))
        raise ValueError(f"manifest parser_status must be one of: {allowed}")

    if not records:
        if parser_status != NO_PARSER_STATUS:
            raise ValueError(
                "empty JSONL is valid only when manifest parser_status is "
                f"'{NO_PARSER_STATUS}'"
            )

        manifest_document_id = manifest.get("document_id")
        if manifest_document_id is not None and manifest_document_id != jsonl_path.stem:
            raise ValueError("manifest document_id does not match JSONL filename")

        manifest_count = manifest.get("records_written")
        if manifest_count is not None and manifest_count != 0:
            raise ValueError("manifest records_written must be 0 for empty JSONL")

        return

    document_ids = {record["document_id"] for record in records}
    if len(document_ids) != 1:
        raise ValueError("all records must share one document_id")

    document_id = next(iter(document_ids))
    if jsonl_path.resolve().stem != document_id:
        raise ValueError("JSONL filename must match document_id")

    manifest_document_id = manifest.get("document_id")
    if manifest_document_id is not None and manifest_document_id != document_id:
        raise ValueError("manifest document_id does not match JSONL records")

    manifest_count = manifest.get("records_written")
    if manifest_count is not None and manifest_count != len(records):
        raise ValueError("manifest records_written does not match JSONL record count")


def main() -> int:
    args = parse_args()
    jsonl_path = args.jsonl_path.resolve()

    try:
        records = read_jsonl(jsonl_path)
        manifest_path = (
            args.manifest_path.resolve()
            if args.manifest_path
            else default_manifest_path(jsonl_path)
        )
        manifest = read_manifest(manifest_path)
        validate_records_for_contract(
            records=records,
            jsonl_path=jsonl_path,
            manifest=manifest,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"invalid: {exc}")
        return 1

    print(f"valid: {jsonl_path}")
    print(f"records_validated: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
