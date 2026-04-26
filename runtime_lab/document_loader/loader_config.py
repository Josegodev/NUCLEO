"""Hardening defaults for the runtime_lab document loader.

These values are conservative placeholders. They exist to make parser
integration safer later, not to define final production policy.
"""

from __future__ import annotations

from pathlib import Path


LAB_DIR = Path(__file__).resolve().parent
RUNTIME_LAB_DIR = LAB_DIR.parent

# Keep the lab parser surface small until a real parser contract is closed.
MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_PAGES = 100
PARSER_TIMEOUT_SECONDS = 10
MAX_RECORDS_PER_DOCUMENT = 1000
MAX_CONTENT_CHARS_PER_RECORD = 256
MAX_TOTAL_CONTENT_CHARS = 100_000

# Empty would mean unrestricted local paths. For HARDENING, keep roots explicit.
ALLOWED_INPUT_ROOTS = (
    Path("/tmp").resolve(),
    RUNTIME_LAB_DIR.resolve(),
)

DEFAULT_OUTPUT_ROOT = RUNTIME_LAB_DIR / "knowledge_store"
PARSER_STATUS_NO_PARSER = "no parser integrated"
