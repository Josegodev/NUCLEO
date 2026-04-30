#!/usr/bin/env python3
"""Audit NUCLEO Markdown documentation against Python contract evidence.

This script is intentionally outside app/. It reads Python files with ast and
Markdown files as text. It must not import or execute AgentService,
AgentRuntime, Planner, PolicyEngine, ToolRegistry, or Tools.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


PROJECT = "NUCLEO"
PHASE = "HARDENING"
OUTPUT_PATH = Path("outputs/audits/docs_contracts_audit.md")
CONTRACT_TERMS = [
    "AgentService",
    "AgentRuntime",
    "Planner",
    "PolicyEngine",
    "ToolRegistry",
    "Tool",
    "AgentRequest",
    "AgentResponse",
    "PolicyDecision",
    "ExecutionContext",
    "dry_run",
]
EXCLUDED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "CONTROL_OPERATIVO",
    "external",
    "node_modules",
    "outputs",
    "venv",
    ".venv",
}
DRY_RUN_NO_EXECUTION_PATTERNS = [
    "no ejecut",
    "no se ejecut",
    "no ejecución",
    "no ejecucion",
    "no llama",
    "nunca llama",
    "sin ejecut",
    "no execution",
    "non-execution",
    "not execut",
    "does not execute",
    "never calls",
    "executed=false",
    '"executed": false',
    "`executed`: false",
    "`executed=False`",
]
POLICY_DECISION_CLOSED_PATTERNS = [
    "policydecisionvalue",
    "enum",
    "closed",
    "cerrad",
    "valor cerrado",
    "valores cerrados",
]


@dataclass(frozen=True)
class PythonSymbol:
    kind: str
    name: str
    path: str
    line: int
    has_docstring: bool


@dataclass
class PythonFileAudit:
    path: str
    has_module_docstring: bool
    parse_error: str | None = None
    symbols: list[PythonSymbol] = field(default_factory=list)
    identifiers: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class MarkdownFileAudit:
    path: str
    mentions: dict[str, list[int]]


class PythonAstVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.symbols: list[PythonSymbol] = []
        self.identifiers: set[str] = set()
        self._class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Record a class definition and continue inspecting its body."""
        self.symbols.append(
            PythonSymbol(
                kind="class",
                name=node.name,
                path=self.path,
                line=node.lineno,
                has_docstring=ast.get_docstring(node, clean=False) is not None,
            )
        )
        self.identifiers.add(node.name)
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Record a function or method definition and its argument names."""
        self._record_callable(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Record an async function or method definition and its arguments."""
        self._record_callable(node)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Record identifier usage without executing the Python module."""
        self.identifiers.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Record attribute names because contract fields may be attributes."""
        self.identifiers.add(node.attr)
        self.generic_visit(node)

    def _record_callable(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        kind = "method" if self._class_stack else "function"
        self.symbols.append(
            PythonSymbol(
                kind=kind,
                name=node.name,
                path=self.path,
                line=node.lineno,
                has_docstring=ast.get_docstring(node, clean=False) is not None,
            )
        )
        self.identifiers.add(node.name)
        for arg in _iter_function_args(node):
            self.identifiers.add(arg.arg)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _iter_repo_files(root: Path, suffix: str) -> list[Path]:
    files = []
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        dirnames[:] = sorted(
            dirname
            for dirname in dirnames
            if dirname not in EXCLUDED_DIR_NAMES
            and not _is_excluded((current_path / dirname).relative_to(root))
        )
        for filename in sorted(filenames):
            if not filename.endswith(suffix):
                continue
            path = current_path / filename
            if not _is_excluded(path.relative_to(root)):
                files.append(path)
    return sorted(files)


def _iter_function_args(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.arg]:
    args = list(node.args.posonlyargs)
    args.extend(node.args.args)
    args.extend(node.args.kwonlyargs)
    if node.args.vararg is not None:
        args.append(node.args.vararg)
    if node.args.kwarg is not None:
        args.append(node.args.kwarg)
    return args


def _audit_python_file(path: Path, root: Path) -> PythonFileAudit:
    relative_path = _relative(path, root)
    text = _read_text(path)

    try:
        tree = ast.parse(text, filename=relative_path)
    except SyntaxError as exc:
        return PythonFileAudit(
            path=relative_path,
            has_module_docstring=False,
            parse_error=f"{exc.msg} at line {exc.lineno}",
        )

    visitor = PythonAstVisitor(relative_path)
    visitor.visit(tree)
    return PythonFileAudit(
        path=relative_path,
        has_module_docstring=ast.get_docstring(tree, clean=False) is not None,
        symbols=visitor.symbols,
        identifiers=visitor.identifiers,
    )


def _find_term_lines(text: str, term: str) -> list[int]:
    pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])")
    return [index for index, line in enumerate(text.splitlines(), start=1) if pattern.search(line)]


def _audit_markdown_file(path: Path, root: Path) -> MarkdownFileAudit:
    text = _read_text(path)
    mentions = {
        term: lines
        for term in CONTRACT_TERMS
        if (lines := _find_term_lines(text, term))
    }
    return MarkdownFileAudit(path=_relative(path, root), mentions=mentions)


def _code_module_keys(path: str) -> set[str]:
    module = path[:-3].replace("/", ".")
    stem = Path(path).stem
    keys = {_normalize_name(module), _normalize_name(stem)}
    if stem == "__init__":
        keys.add(_normalize_name(str(Path(path).parent).replace("/", ".")))
    return keys


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _documented_modules(markdown_files: list[MarkdownFileAudit]) -> dict[str, list[str]]:
    modules: dict[str, list[str]] = {}
    module_path_pattern = re.compile(r"\b(?:app|runtime_lab|scripts|tests)(?:\.[A-Za-z_]\w*)+\b")

    for md_file in markdown_files:
        path = Path(md_file.path)
        if len(path.parts) >= 3 and path.parts[-2] == "modules":
            modules.setdefault(path.stem, []).append(md_file.path)

        text = _read_text(_repo_root() / md_file.path)
        for match in module_path_pattern.finditer(text):
            modules.setdefault(match.group(0), []).append(md_file.path)

    return modules


def _contract_code_evidence(
    term: str,
    python_files: list[PythonFileAudit],
) -> list[str]:
    evidence: list[str] = []
    for py_file in python_files:
        for symbol in py_file.symbols:
            if symbol.name == term:
                evidence.append(f"{symbol.path}:{symbol.line} {symbol.kind} `{symbol.name}`")
            elif term == "Tool" and symbol.kind == "class" and symbol.name.endswith("Tool"):
                evidence.append(f"{symbol.path}:{symbol.line} class `{symbol.name}`")
        if term in py_file.identifiers:
            evidence.append(f"{py_file.path} identifier `{term}`")
    return sorted(set(evidence))


def _term_doc_files(
    term: str,
    markdown_files: list[MarkdownFileAudit],
) -> list[str]:
    return [md_file.path for md_file in markdown_files if term in md_file.mentions]


def _markdown_missing_dry_run_no_execution(root: Path, files: list[MarkdownFileAudit]) -> list[str]:
    missing: list[str] = []
    for md_file in files:
        if "dry_run" not in md_file.mentions:
            continue
        normalized = _read_text(root / md_file.path).lower().replace(" ", "")
        spaced = _read_text(root / md_file.path).lower()
        if not any(pattern in normalized or pattern in spaced for pattern in DRY_RUN_NO_EXECUTION_PATTERNS):
            missing.append(md_file.path)
    return missing


def _markdown_missing_policy_decision_closed(root: Path, files: list[MarkdownFileAudit]) -> list[str]:
    missing: list[str] = []
    for md_file in files:
        if "PolicyDecision" not in md_file.mentions:
            continue
        normalized = _read_text(root / md_file.path).lower()
        if not any(pattern in normalized for pattern in POLICY_DECISION_CLOSED_PATTERNS):
            missing.append(md_file.path)
    return missing


def _public_callables_without_docstrings(
    python_files: list[PythonFileAudit],
) -> list[PythonSymbol]:
    missing = []
    for py_file in python_files:
        for symbol in py_file.symbols:
            if symbol.kind not in {"function", "method"}:
                continue
            if symbol.name.startswith("_"):
                continue
            if symbol.has_docstring:
                continue
            missing.append(symbol)
    return sorted(missing, key=lambda item: (item.path, item.line, item.name))


def _module_files_without_docstrings(python_files: list[PythonFileAudit]) -> list[str]:
    return [
        py_file.path
        for py_file in python_files
        if py_file.parse_error is None and not py_file.has_module_docstring
    ]


def _format_lines(items: list[str], empty: str = "None detected.") -> list[str]:
    if not items:
        return [empty]
    return [f"- `{item}`" for item in items]


def _format_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    if not rows:
        return ["None detected."]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def _build_report(
    root: Path,
    python_files: list[PythonFileAudit],
    markdown_files: list[MarkdownFileAudit],
) -> str:
    all_symbols = [symbol for py_file in python_files for symbol in py_file.symbols]
    class_symbols = [symbol for symbol in all_symbols if symbol.kind == "class"]
    public_missing_docstrings = _public_callables_without_docstrings(python_files)
    module_missing_docstrings = _module_files_without_docstrings(python_files)
    parse_errors = [py_file for py_file in python_files if py_file.parse_error is not None]

    code_key_set: set[str] = set()
    for py_file in python_files:
        code_key_set.update(_code_module_keys(py_file.path))
        code_key_set.update(_normalize_name(symbol.name) for symbol in py_file.symbols)

    documented_modules = _documented_modules(markdown_files)
    missing_documented_modules = [
        f"{module} (mentioned in {', '.join(sorted(set(paths)))})"
        for module, paths in sorted(documented_modules.items())
        if _normalize_name(module) not in code_key_set
    ]

    missing_doc_contracts = []
    contract_rows = []
    for term in CONTRACT_TERMS:
        doc_files = _term_doc_files(term, markdown_files)
        code_evidence = _contract_code_evidence(term, python_files)
        if doc_files and not code_evidence:
            missing_doc_contracts.append(
                f"{term} (mentioned in {len(doc_files)} Markdown file(s))"
            )
        contract_rows.append(
            [
                f"`{term}`",
                str(len(doc_files)),
                str(len(code_evidence)),
                "; ".join(code_evidence[:3]) if code_evidence else "not found",
            ]
        )

    dry_run_missing = _markdown_missing_dry_run_no_execution(root, markdown_files)
    policy_decision_missing = _markdown_missing_policy_decision_closed(root, markdown_files)

    markdown_rows = []
    for md_file in markdown_files:
        if not md_file.mentions:
            continue
        terms = ", ".join(f"`{term}`" for term in sorted(md_file.mentions))
        lines = ", ".join(
            f"{term}: {md_file.mentions[term][:5]}"
            for term in sorted(md_file.mentions)
        )
        markdown_rows.append([f"`{md_file.path}`", terms, lines])

    class_rows = [
        [f"`{symbol.name}`", f"`{symbol.path}:{symbol.line}`"]
        for symbol in sorted(class_symbols, key=lambda item: (item.name, item.path))
    ]

    missing_public_rows = [
        [symbol.kind, f"`{symbol.name}`", f"`{symbol.path}:{symbol.line}`"]
        for symbol in public_missing_docstrings
    ]

    parse_error_rows = [
        [f"`{py_file.path}`", py_file.parse_error or ""]
        for py_file in parse_errors
    ]

    lines = [
        "# NUCLEO Docs Contracts Audit",
        "",
        "## Scope",
        "",
        f"- Project: {PROJECT}",
        f"- Phase: {PHASE}",
        "- Audit mode: read Python with ast, read Markdown as text, write Markdown report only.",
        "- Runtime integration: none.",
        "- Forbidden runtime access: AgentService, AgentRuntime, Planner, PolicyEngine, ToolRegistry, Tools.",
        "- Excluded paths include CONTROL_OPERATIVO.",
        "",
        "## Python Inventory",
        "",
        f"- Python files inspected: {len(python_files)}",
        f"- Python parse errors: {len(parse_errors)}",
        f"- Classes discovered: {len(class_symbols)}",
        f"- Functions and methods discovered: {len([s for s in all_symbols if s.kind in {'function', 'method'}])}",
        "",
        "### Classes",
        "",
        *_format_table(["Class", "Evidence"], class_rows),
        "",
        "### Parse Errors",
        "",
        *_format_table(["File", "Error"], parse_error_rows),
        "",
        "## Markdown Inventory",
        "",
        f"- Markdown files inspected: {len(markdown_files)}",
        f"- Markdown files with contract mentions: {len(markdown_rows)}",
        "",
        *_format_table(["File", "Terms", "Lines"], markdown_rows),
        "",
        "## Contract Mentions",
        "",
        *_format_table(
            ["Contract", "Markdown files", "Python evidence count", "Python evidence sample"],
            contract_rows,
        ),
        "",
        "## Potential Drift",
        "",
        "### Documented Modules Not Found In Code",
        "",
        *_format_lines(missing_documented_modules),
        "",
        "### Contracts Mentioned In Docs But Not Found In Code",
        "",
        *_format_lines(missing_doc_contracts),
        "",
        "### Markdown Mentions dry_run Without Non-Execution Evidence",
        "",
        *_format_lines(dry_run_missing),
        "",
        "### Markdown Mentions PolicyDecision Without Closed Enum/Value Evidence",
        "",
        *_format_lines(policy_decision_missing),
        "",
        "## Missing Docstrings",
        "",
        "### Python Files Without Module Docstring",
        "",
        *_format_lines(module_missing_docstrings),
        "",
        "### Public Functions Or Methods Without Docstring",
        "",
        *_format_table(["Kind", "Name", "Evidence"], missing_public_rows),
        "",
        "## Open Hardening Topics",
        "",
    ]

    hardening_topics = []
    if missing_documented_modules:
        hardening_topics.append("Review documented modules that have no matching Python module or symbol.")
    if missing_doc_contracts:
        hardening_topics.append("Review contract names mentioned in Markdown without Python evidence.")
    if dry_run_missing:
        hardening_topics.append("Clarify dry_run documentation where non-execution is not explicit.")
    if policy_decision_missing:
        hardening_topics.append("Clarify PolicyDecision documentation where closed enum/value wording is missing.")
    if module_missing_docstrings or public_missing_docstrings:
        hardening_topics.append("Decide which public Python surfaces need docstrings during HARDENING.")
    if not hardening_topics:
        hardening_topics.append("No open hardening topics detected by this audit.")

    lines.extend(f"- {topic}" for topic in hardening_topics)
    lines.extend(
        [
            "",
            "## Recommended Documentation Updates",
            "",
        ]
    )

    recommendations = []
    if dry_run_missing:
        recommendations.append(
            "For each flagged dry_run Markdown file, state whether dry_run avoids calling tool.run(...)."
        )
    if policy_decision_missing:
        recommendations.append(
            "For each flagged PolicyDecision Markdown file, state that decision uses PolicyDecisionValue.ALLOW or PolicyDecisionValue.DENY."
        )
    if missing_documented_modules:
        recommendations.append(
            "For each documented module without code evidence, either point to the real Python file or mark it as historical/experimental."
        )
    if missing_doc_contracts:
        recommendations.append(
            "For each documented contract without code evidence, either align the name with code or mark the mention as conceptual."
        )
    if module_missing_docstrings or public_missing_docstrings:
        recommendations.append(
            "Use the missing docstring list as review evidence; do not add docstrings mechanically unless they close a real contract."
        )
    if not recommendations:
        recommendations.append("No documentation updates recommended by this audit.")

    lines.extend(f"- {recommendation}" for recommendation in recommendations)
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Run the documentation contract audit and write the Markdown report."""
    root = _repo_root()
    python_files = [_audit_python_file(path, root) for path in _iter_repo_files(root, ".py")]
    markdown_files = [_audit_markdown_file(path, root) for path in _iter_repo_files(root, ".md")]

    report = _build_report(root, python_files, markdown_files)
    output_path = root / OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Wrote {output_path.relative_to(root).as_posix()}")


if __name__ == "__main__":
    main()
