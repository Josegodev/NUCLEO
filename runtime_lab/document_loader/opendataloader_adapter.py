"""Disabled OpenDataLoader adapter stub.

This module intentionally avoids loading the OpenDataLoader package. It only
reserves an adapter boundary for future review.
"""

from __future__ import annotations

from pathlib import Path

from loader_config import PARSER_STATUS_NO_PARSER
from parser_adapter import BasePdfParser, ParserError, ParserResult


class OpenDataLoaderPdfParser(BasePdfParser):
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    def parse(
        self,
        pdf_path: Path,
        *,
        document_id: str,
        source_path: Path,
        created_at: str,
    ) -> ParserResult:
        if not self.enabled:
            return ParserResult(
                parser_status=PARSER_STATUS_NO_PARSER,
                records=[],
                errors=[
                    ParserError(
                        code="parser_disabled",
                        message="OpenDataLoader adapter is declared but disabled",
                        severity="warning",
                        recoverable=True,
                        source="parser",
                    )
                ],
            )

        return ParserResult(
            parser_status="parser_error",
            records=[],
            errors=[
                ParserError(
                    code="parser_not_integrated",
                    message=(
                        "OpenDataLoader adapter was enabled, but no parser "
                        "implementation is integrated"
                    ),
                    severity="error",
                    recoverable=True,
                    source="parser",
                )
            ],
        )
