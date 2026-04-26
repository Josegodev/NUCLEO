from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


DOC_LOADER_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DOC_LOADER_DIR.parents[1]
if str(DOC_LOADER_DIR) not in sys.path:
    sys.path.insert(0, str(DOC_LOADER_DIR))

from loader_config import PARSER_STATUS_NO_PARSER
from parser_adapter import NoOpPdfParser


OpenDataLoaderPdfParser = importlib.import_module(
    "opendataloader_adapter"
).OpenDataLoaderPdfParser
LOAD_SCRIPT = DOC_LOADER_DIR / "load_pdf_to_jsonl.py"
VALIDATE_SCRIPT = DOC_LOADER_DIR / "validate_jsonl_contract.py"
BATCH_SCRIPT = DOC_LOADER_DIR / "batch_smoke_test.py"
FIXTURES_DIR = DOC_LOADER_DIR / "fixtures"


def parse_stdout_pairs(stdout: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in stdout.splitlines():
        if ": " not in line:
            continue

        key, value = line.split(": ", 1)
        values[key] = value

    return values


def run_script(*args: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *(str(arg) for arg in args)],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


class NoOpPdfParserTests(unittest.TestCase):
    def test_noop_parser_returns_no_parser_status(self) -> None:
        result = NoOpPdfParser().parse(
            Path("/tmp/synthetic.pdf"),
            document_id="a" * 64,
            source_path=Path("/tmp/synthetic.pdf"),
            created_at="1970-01-01T00:00:00Z",
        )

        self.assertEqual(result.parser_status, PARSER_STATUS_NO_PARSER)

    def test_noop_parser_returns_empty_records(self) -> None:
        result = NoOpPdfParser().parse(
            Path("/tmp/synthetic.pdf"),
            document_id="a" * 64,
            source_path=Path("/tmp/synthetic.pdf"),
            created_at="1970-01-01T00:00:00Z",
        )

        self.assertEqual(result.records, [])

    def test_noop_parser_emits_parser_unavailable_warning(self) -> None:
        result = NoOpPdfParser().parse(
            Path("/tmp/synthetic.pdf"),
            document_id="a" * 64,
            source_path=Path("/tmp/synthetic.pdf"),
            created_at="1970-01-01T00:00:00Z",
        )

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].code, "parser_unavailable")
        self.assertEqual(result.errors[0].severity, "warning")
        self.assertTrue(result.errors[0].recoverable)


class OpenDataLoaderAdapterTests(unittest.TestCase):
    def test_opendataloader_adapter_default_is_disabled(self) -> None:
        parser = OpenDataLoaderPdfParser()

        self.assertFalse(parser.enabled)

    def test_disabled_opendataloader_adapter_does_not_parse(self) -> None:
        result = OpenDataLoaderPdfParser(enabled=False).parse(
            Path("/tmp/synthetic.pdf"),
            document_id="a" * 64,
            source_path=Path("/tmp/synthetic.pdf"),
            created_at="1970-01-01T00:00:00Z",
        )

        self.assertEqual(result.parser_status, PARSER_STATUS_NO_PARSER)
        self.assertEqual(result.records, [])

    def test_disabled_opendataloader_adapter_returns_parser_disabled(self) -> None:
        result = OpenDataLoaderPdfParser(enabled=False).parse(
            Path("/tmp/synthetic.pdf"),
            document_id="a" * 64,
            source_path=Path("/tmp/synthetic.pdf"),
            created_at="1970-01-01T00:00:00Z",
        )

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].code, "parser_disabled")
        self.assertEqual(result.errors[0].severity, "warning")

    def test_opendataloader_package_import_is_not_required(self) -> None:
        self.assertNotIn("opendataloader", sys.modules)

    def test_no_active_opendataloader_import_strings_exist(self) -> None:
        blocked_patterns = [
            "import " + "opendataloader",
            "from " + "opendataloader",
            "import " + "OpenDataLoader",
            "from " + "OpenDataLoader",
        ]

        for path in DOC_LOADER_DIR.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue

            content = path.read_text(encoding="utf-8")
            for pattern in blocked_patterns:
                self.assertNotIn(pattern, content, f"{pattern} found in {path}")


class JsonlContractValidationTests(unittest.TestCase):
    def test_valid_empty_jsonl_is_accepted(self) -> None:
        result = run_script(VALIDATE_SCRIPT, FIXTURES_DIR / "valid_empty.jsonl")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("records_validated: 0", result.stdout)

    def test_invalid_block_type_is_rejected(self) -> None:
        result = run_script(VALIDATE_SCRIPT, FIXTURES_DIR / "invalid_block_type.jsonl")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("block_type", result.stdout)

    def test_invalid_content_hash_is_rejected(self) -> None:
        result = run_script(
            VALIDATE_SCRIPT,
            FIXTURES_DIR / "invalid_content_hash.jsonl",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("content_hash does not match content", result.stdout)


class LoaderBehaviorTests(unittest.TestCase):
    def test_loader_rejects_non_pdf_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "not_pdf.txt"
            input_path.write_text("not a pdf\n", encoding="utf-8")

            result = run_script(
                LOAD_SCRIPT,
                input_path,
                "--knowledge-store-dir",
                temp_path / "knowledge_store",
            )
            stdout = parse_stdout_pairs(result.stdout)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(stdout["error_code"], "non_pdf_input")

    def test_loader_rejects_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            missing_path = temp_path / "missing.pdf"

            result = run_script(
                LOAD_SCRIPT,
                missing_path,
                "--knowledge-store-dir",
                temp_path / "knowledge_store",
            )
            stdout = parse_stdout_pairs(result.stdout)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(stdout["error_code"], "invalid_path")

    def test_loader_accepts_temp_pdf_and_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / "synthetic.pdf"
            pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
            store_path = temp_path / "knowledge_store"

            result = run_script(
                LOAD_SCRIPT,
                pdf_path,
                "--knowledge-store-dir",
                store_path,
            )
            stdout = parse_stdout_pairs(result.stdout)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(stdout["records_written"], "0")
            self.assertEqual(stdout["parser_status"], PARSER_STATUS_NO_PARSER)

            jsonl_path = Path(stdout["output_jsonl"])
            manifest_path = Path(stdout["output_manifest"])
            context_path = Path(stdout["output_context_md"])

            self.assertTrue(jsonl_path.exists())
            self.assertTrue(manifest_path.exists())
            self.assertTrue(context_path.exists())
            self.assertEqual(jsonl_path.read_text(encoding="utf-8"), "")

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["records_written"], 0)
            self.assertEqual(manifest["parser_status"], PARSER_STATUS_NO_PARSER)
            self.assertEqual(manifest["errors"][0]["code"], "parser_unavailable")
            self.assertIn(
                "No parser integrated yet.",
                context_path.read_text(encoding="utf-8"),
            )

    def test_default_loader_still_uses_noop_parser(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / "synthetic.pdf"
            pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")

            result = run_script(
                LOAD_SCRIPT,
                pdf_path,
                "--knowledge-store-dir",
                temp_path / "knowledge_store",
            )
            stdout = parse_stdout_pairs(result.stdout)
            manifest = json.loads(
                Path(stdout["output_manifest"]).read_text(encoding="utf-8")
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(manifest["errors"][0]["code"], "parser_unavailable")
            self.assertNotEqual(manifest["errors"][0]["code"], "parser_disabled")



class BatchSmokeTestTests(unittest.TestCase):
    def test_batch_smoke_rejects_missing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_dir = Path(temp_dir) / "missing"

            result = run_script(BATCH_SCRIPT, missing_dir)
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["status"], "rejected")
            self.assertEqual(payload["error_code"], "invalid_directory")


if __name__ == "__main__":
    unittest.main()
