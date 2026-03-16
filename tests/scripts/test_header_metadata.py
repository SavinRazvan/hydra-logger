"""
Role: Pytest coverage for test header metadata behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - ast
 - pathlib
 - re
Notes:
 - Validates test header metadata behavior, edge cases, and regression safety.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = ("hydra_logger", "scripts", "examples", "tests")
FORBIDDEN_TERMS = ("(update when known)", "placeholder", "tbd", "todo")
FIELD_PATTERN = re.compile(r"^\s*(Role|Used By|Depends On|Notes):")


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()

    for root_name in SCAN_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if ".hydra_env" in path.parts:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(path)

    for path in ROOT.glob("*.py"):
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        files.append(path)

    return sorted(files)


def _header_lines(docstring: str) -> list[str]:
    lines = []
    for line in docstring.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("-") or FIELD_PATTERN.match(stripped):
            lines.append(stripped.lower())
    return lines


def test_header_fields_do_not_contain_placeholder_terms() -> None:
    violations: list[str] = []

    for path in _iter_python_files():
        source = path.read_text(encoding="utf-8")
        module = ast.parse(source)
        doc = ast.get_docstring(module, clean=False)
        if not doc:
            continue

        lines = _header_lines(doc)
        if not lines:
            continue

        for line in lines:
            for term in FORBIDDEN_TERMS:
                if term in line:
                    relative_path = path.relative_to(ROOT).as_posix()
                    violations.append(f"{relative_path}: contains '{term}' in header")
                    break

    assert not violations, "Header placeholder terms found:\n" + "\n".join(violations)
