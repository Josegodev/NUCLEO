"""Parser adapter boundary for runtime_lab document loading.

No real PDF parser is integrated here. The current adapter is a no-op that
returns an explicit parser_unavailable warning without inventing content.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from loader_config import PARSER_STATUS_NO_PARSER


@dataclass(frozen=True)
class ParserError:
    code: str
    message: str
    severity: str
    recoverable: bool
    source: str

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "recoverable": self.recoverable,
            "source": self.source,
        }


@dataclass(frozen=True)
class ParserResult:
    parser_status: str
    records: list[dict[str, object]]
    errors: list[ParserError]


class BasePdfParser(Protocol):
    def parse(
        self,
        pdf_path: Path,
        *,
        document_id: str,
        source_path: Path,
        created_at: str,
    ) -> ParserResult:
        """Parse a local PDF path into normalized records."""


class NoOpPdfParser:
    def parse(
        self,
        pdf_path: Path,
        *,
        document_id: str,
        source_path: Path,
        created_at: str,
    ) -> ParserResult:
        return ParserResult(
            parser_status=PARSER_STATUS_NO_PARSER,
            records=[],
            errors=[
                ParserError(
                    code="parser_unavailable",
                    message="no PDF parser is integrated; no extraction was attempted",
                    severity="warning",
                    recoverable=True,
                    source="parser",
                )
            ],
        )
