"""Batch smoke runner for local PDF folders.

This script stays in runtime_lab and delegates each PDF to the existing loader.
It does not parse PDF content itself and does not call LLMs or network services.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from loader_config import ALLOWED_INPUT_ROOTS
from loader_config import DEFAULT_OUTPUT_ROOT


LAB_DIR = Path(__file__).resolve().parent
LOADER_SCRIPT = LAB_DIR / "load_pdf_to_jsonl.py"


class BatchInputError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run document_loader smoke tests for a local PDF folder.",
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing local .pdf smoke inputs.",
    )
    parser.add_argument(
        "--knowledge-store-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Directory for generated loader outputs.",
    )
    return parser.parse_args()


def resolve_input_dir(input_dir: Path) -> Path:
    resolved_dir = input_dir.expanduser().resolve(strict=False)

    if not resolved_dir.exists():
        raise BatchInputError(
            "invalid_directory",
            f"input directory does not exist: {resolved_dir}",
        )

    if not resolved_dir.is_dir():
        raise BatchInputError(
            "not_a_directory",
            f"input path is not a directory: {resolved_dir}",
        )

    if ALLOWED_INPUT_ROOTS and not is_inside_allowed_roots(resolved_dir):
        roots = ", ".join(str(root) for root in ALLOWED_INPUT_ROOTS)
        raise BatchInputError(
            "directory_outside_allowed_roots",
            (
                "input directory is outside configured ALLOWED_INPUT_ROOTS: "
                f"{resolved_dir}; allowed roots: {roots}"
            ),
        )

    return resolved_dir


def is_inside_allowed_roots(path: Path) -> bool:
    for root in ALLOWED_INPUT_ROOTS:
        resolved_root = root.resolve()
        if path == resolved_root or resolved_root in path.parents:
            return True

    return False


def find_pdf_files(input_dir: Path) -> list[Path]:
    return sorted(
        (path for path in input_dir.rglob("*.pdf") if path.is_file()),
        key=lambda path: path.relative_to(input_dir).as_posix(),
    )


def parse_loader_stdout(stdout: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in stdout.splitlines():
        if ": " not in line:
            continue

        key, value = line.split(": ", 1)
        values[key] = value

    return values


def run_loader(pdf_path: Path, knowledge_store_dir: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            str(LOADER_SCRIPT),
            str(pdf_path),
            "--knowledge-store-dir",
            str(knowledge_store_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    parsed_stdout = parse_loader_stdout(result.stdout)
    return {
        "returncode": result.returncode,
        "stdout": parsed_stdout,
        "stderr": result.stderr.strip(),
    }


def build_summary(input_dir: Path, knowledge_store_dir: Path) -> dict[str, Any]:
    pdf_paths = find_pdf_files(input_dir)
    document_ids: list[str] = []
    parser_status_by_file: dict[str, str | None] = {}
    records_written_by_file: dict[str, int | None] = {}
    error_codes_by_file: dict[str, list[str]] = {}
    succeeded = 0
    failed = 0

    for pdf_path in pdf_paths:
        relative_path = pdf_path.relative_to(input_dir).as_posix()
        loader_result = run_loader(pdf_path, knowledge_store_dir)
        stdout = loader_result["stdout"]

        if loader_result["returncode"] == 0:
            succeeded += 1
        else:
            failed += 1

        document_id = stdout.get("document_id")
        if document_id:
            document_ids.append(document_id)

        parser_status_by_file[relative_path] = stdout.get("parser_status")
        records_written_by_file[relative_path] = parse_optional_int(
            stdout.get("records_written")
        )
        error_code = stdout.get("error_code")
        error_codes_by_file[relative_path] = [error_code] if error_code else []

    return {
        "total_pdfs": len(pdf_paths),
        "succeeded": succeeded,
        "failed": failed,
        "document_ids": document_ids,
        "parser_status_by_file": parser_status_by_file,
        "records_written_by_file": records_written_by_file,
        "error_codes_by_file": error_codes_by_file,
    }


def parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True))


def main() -> int:
    args = parse_args()

    try:
        input_dir = resolve_input_dir(args.input_dir)
    except BatchInputError as exc:
        print_json(
            {
                "status": "rejected",
                "error_code": exc.code,
                "error_message": exc.message,
            }
        )
        return 1

    summary = build_summary(input_dir, args.knowledge_store_dir)
    print_json(summary)
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
