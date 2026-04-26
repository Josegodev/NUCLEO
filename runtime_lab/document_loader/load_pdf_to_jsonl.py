"""Local PDF-to-JSONL ingestion scaffold for runtime_lab only.

This script intentionally does not import NUCLEO runtime modules. It prepares
stable local artifacts for external LLM context experiments and writes real
parser blocks only when a parser is integrated here in the lab.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from build_llm_context import build_context_markdown
from build_llm_context import write_text_file
from loader_config import ALLOWED_INPUT_ROOTS
from loader_config import DEFAULT_OUTPUT_ROOT
from loader_config import MAX_CONTENT_CHARS_PER_RECORD
from loader_config import MAX_PDF_BYTES
from loader_config import MAX_PAGES
from loader_config import MAX_RECORDS_PER_DOCUMENT
from loader_config import MAX_TOTAL_CONTENT_CHARS
from loader_config import PARSER_TIMEOUT_SECONDS
from parser_adapter import BasePdfParser
from parser_adapter import NoOpPdfParser
from parser_adapter import ParserResult
from validate_jsonl_contract import validate_records_for_contract


DEFAULT_CREATED_AT = "1970-01-01T00:00:00Z"
PARSER_STATUS_INPUT_ERROR = "input_error"
PARSER_STATUS_PARSER_ERROR = "parser_error"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize a local PDF into deterministic JSONL records.",
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the input PDF.",
    )
    parser.add_argument(
        "--knowledge-store-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Directory for generated JSONL, manifest, and context files.",
    )
    parser.add_argument(
        "--created-at",
        default=DEFAULT_CREATED_AT,
        help=(
            "Metadata timestamp for future JSONL records. The default is "
            "deterministic for lab reproducibility."
        ),
    )
    return parser.parse_args()


class LoaderInputError(Exception):
    def __init__(self, error: dict[str, object]) -> None:
        self.error = error
        super().__init__(str(error["message"]))


def normalized_error(
    *,
    code: str,
    message: str,
    severity: str = "error",
    recoverable: bool = True,
    source: str = "input_validation",
) -> dict[str, object]:
    return {
        "code": code,
        "message": message,
        "severity": severity,
        "recoverable": recoverable,
        "source": source,
    }


def build_limits_snapshot() -> dict[str, object]:
    return {
        "max_pdf_bytes": MAX_PDF_BYTES,
        "max_pages": MAX_PAGES,
        "parser_timeout_seconds": PARSER_TIMEOUT_SECONDS,
        "max_records_per_document": MAX_RECORDS_PER_DOCUMENT,
        "max_content_chars_per_record": MAX_CONTENT_CHARS_PER_RECORD,
        "max_total_content_chars": MAX_TOTAL_CONTENT_CHARS,
        "allowed_input_roots": [str(root) for root in ALLOWED_INPUT_ROOTS],
    }


def validate_pdf_path(pdf_path: Path) -> Path:
    resolved_path = pdf_path.expanduser().resolve(strict=False)

    if not resolved_path.exists():
        raise LoaderInputError(
            normalized_error(
                code="invalid_path",
                message=f"input PDF does not exist: {resolved_path}",
            )
        )

    if not resolved_path.is_file():
        raise LoaderInputError(
            normalized_error(
                code="invalid_path",
                message=f"input path is not a file: {resolved_path}",
            )
        )

    if resolved_path.suffix.lower() != ".pdf":
        raise LoaderInputError(
            normalized_error(
                code="non_pdf_input",
                message=f"input path must have a .pdf suffix: {resolved_path}",
            )
        )

    if ALLOWED_INPUT_ROOTS and not is_inside_allowed_roots(resolved_path):
        roots = ", ".join(str(root) for root in ALLOWED_INPUT_ROOTS)
        raise LoaderInputError(
            normalized_error(
                code="path_outside_allowed_roots",
                message=(
                    "input path is outside configured ALLOWED_INPUT_ROOTS: "
                    f"{resolved_path}; allowed roots: {roots}"
                ),
            )
        )

    file_size = resolved_path.stat().st_size
    if file_size > MAX_PDF_BYTES:
        raise LoaderInputError(
            normalized_error(
                code="file_too_large",
                message=(
                    "input PDF exceeds MAX_PDF_BYTES: "
                    f"{file_size} > {MAX_PDF_BYTES}"
                ),
            )
        )

    return resolved_path


def is_inside_allowed_roots(path: Path) -> bool:
    for root in ALLOWED_INPUT_ROOTS:
        resolved_root = root.resolve()
        if path == resolved_root or resolved_root in path.parents:
            return True

    return False


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def compute_document_id(pdf_path: Path) -> str:
    return sha256_bytes(pdf_path.read_bytes())


def build_output_paths(
    document_id: str,
    knowledge_store_dir: Path,
) -> dict[str, Path]:
    store_dir = knowledge_store_dir.resolve()
    return {
        "jsonl": store_dir / "documents" / f"{document_id}.jsonl",
        "manifest": store_dir / "manifests" / f"{document_id}.manifest.json",
        "context": store_dir / "llm_context" / f"{document_id}.context.md",
    }


def build_error_manifest_path(
    attempted_pdf_path: Path,
    knowledge_store_dir: Path,
) -> Path:
    attempted_path = attempted_pdf_path.expanduser().resolve(strict=False)
    path_hash = sha256_text(str(attempted_path))
    return (
        knowledge_store_dir.resolve()
        / "manifests"
        / f"input-error-{path_hash}.manifest.json"
    )


def parse_pdf_with_adapter(
    parser: BasePdfParser,
    *,
    document_id: str,
    source_path: Path,
    created_at: str,
) -> ParserResult:
    return parser.parse(
        source_path,
        document_id=document_id,
        source_path=source_path,
        created_at=created_at,
    )


def build_manifest(
    *,
    document_id: str | None,
    source_path: Path,
    parser_status: str,
    records_written: int,
    output_jsonl: Path | None,
    output_context_md: Path | None,
    errors: list[dict[str, object]],
) -> dict[str, object]:
    limits = build_limits_snapshot()
    return {
        "document_id": document_id,
        "source_path": str(source_path),
        "source_hash": document_id,
        "parser_status": parser_status,
        "records_written": records_written,
        "output_jsonl": str(output_jsonl) if output_jsonl else None,
        "output_context_md": str(output_context_md) if output_context_md else None,
        "limits": limits,
        "parser_timeout_seconds": limits["parser_timeout_seconds"],
        "max_records_per_document": limits["max_records_per_document"],
        "max_content_chars_per_record": limits["max_content_chars_per_record"],
        "max_total_content_chars": limits["max_total_content_chars"],
        "errors": errors,
    }


def write_jsonl(output_path: Path, records: Iterable[dict[str, object]]) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    count = 0

    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True))
            handle.write("\n")
            count += 1

    temp_path.replace(output_path)
    return count


def write_manifest(output_path: Path, manifest: dict[str, object]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")
    temp_path.replace(output_path)


def validate_adapter_output_before_write(
    *,
    parser_result: ParserResult,
    document_id: str,
    source_path: Path,
    output_jsonl: Path,
    output_context_md: Path,
) -> dict[str, object]:
    manifest = build_manifest(
        document_id=document_id,
        source_path=source_path,
        parser_status=parser_result.parser_status,
        records_written=len(parser_result.records),
        output_jsonl=output_jsonl,
        output_context_md=output_context_md,
        errors=[error.to_dict() for error in parser_result.errors],
    )
    validate_records_for_contract(
        records=parser_result.records,
        jsonl_path=output_jsonl,
        manifest=manifest,
    )
    return manifest


def write_parser_contract_failure_manifest(
    *,
    source_pdf: Path,
    output_manifest: Path,
    output_jsonl: Path,
    output_context_md: Path,
    document_id: str,
    error_message: str,
) -> None:
    manifest = build_manifest(
        document_id=document_id,
        source_path=source_pdf,
        parser_status=PARSER_STATUS_PARSER_ERROR,
        records_written=0,
        output_jsonl=output_jsonl,
        output_context_md=output_context_md,
        errors=[
            normalized_error(
                code="parser_failed",
                message=(
                    "parser adapter output failed contract validation: "
                    f"{error_message}"
                ),
                severity="error",
                recoverable=True,
                source="parser",
            )
        ],
    )
    write_manifest(output_manifest, manifest)


def write_rejected_input_manifest(
    *,
    attempted_pdf_path: Path,
    knowledge_store_dir: Path,
    error: dict[str, object],
) -> Path:
    manifest_path = build_error_manifest_path(
        attempted_pdf_path=attempted_pdf_path,
        knowledge_store_dir=knowledge_store_dir,
    )
    manifest = build_manifest(
        document_id=None,
        source_path=attempted_pdf_path.expanduser().resolve(strict=False),
        parser_status=PARSER_STATUS_INPUT_ERROR,
        records_written=0,
        output_jsonl=None,
        output_context_md=None,
        errors=[error],
    )
    write_manifest(manifest_path, manifest)
    return manifest_path


def print_rejected_input(
    *,
    manifest_path: Path,
    error: dict[str, Any],
) -> None:
    print("status: rejected")
    print(f"output_manifest: {manifest_path}")
    print(f"error_code: {error['code']}")
    print(f"error_message: {error['message']}")


def main() -> int:
    args = parse_args()

    try:
        source_pdf = validate_pdf_path(args.pdf_path)
    except LoaderInputError as exc:
        manifest_path = write_rejected_input_manifest(
            attempted_pdf_path=args.pdf_path,
            knowledge_store_dir=args.knowledge_store_dir,
            error=exc.error,
        )
        print_rejected_input(manifest_path=manifest_path, error=exc.error)
        return 1

    document_id = compute_document_id(source_pdf)
    output_paths = build_output_paths(
        document_id=document_id,
        knowledge_store_dir=args.knowledge_store_dir,
    )
    parser_result = parse_pdf_with_adapter(
        NoOpPdfParser(),
        document_id=document_id,
        source_path=source_pdf,
        created_at=args.created_at,
    )
    try:
        manifest = validate_adapter_output_before_write(
            parser_result=parser_result,
            document_id=document_id,
            source_path=source_pdf,
            output_jsonl=output_paths["jsonl"],
            output_context_md=output_paths["context"],
        )
    except ValueError as exc:
        write_parser_contract_failure_manifest(
            source_pdf=source_pdf,
            output_manifest=output_paths["manifest"],
            output_jsonl=output_paths["jsonl"],
            output_context_md=output_paths["context"],
            document_id=document_id,
            error_message=str(exc),
        )
        print("status: rejected")
        print(f"output_manifest: {output_paths['manifest']}")
        print("error_code: parser_failed")
        print(f"error_message: {exc}")
        return 1

    records = parser_result.records
    records_written = write_jsonl(output_paths["jsonl"], records)
    context_markdown = build_context_markdown(
        document_id=document_id,
        records=records,
        parser_status=parser_result.parser_status,
        records_written=records_written,
        source_path=str(source_pdf),
    )
    write_text_file(output_paths["context"], context_markdown)
    write_manifest(output_paths["manifest"], manifest)

    print(f"source_pdf: {source_pdf}")
    print(f"document_id: {document_id}")
    print(f"output_jsonl: {output_paths['jsonl']}")
    print(f"output_manifest: {output_paths['manifest']}")
    print(f"output_context_md: {output_paths['context']}")
    print(f"records_written: {records_written}")
    print(f"parser_status: {parser_result.parser_status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
