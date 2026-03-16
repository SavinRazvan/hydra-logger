"""
Role: Repository automation for check slim headers.
Used By:
 - Repository maintainers invoking automation commands.
Depends On:
 - argparse
 - ast
 - json
 - pathlib
 - re
 - subprocess
 - typing
Notes:
 - Implements PR workflow automation for check slim headers actions.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ALLOWED_FIELDS = {"Role", "Used By", "Depends On", "Notes"}
REQUIRED_FIELDS = {"Role", "Used By", "Depends On", "Notes"}
DISALLOWED_FIELDS = {"File", "Path"}
FIELD_PATTERN = re.compile(r"^\s*([A-Za-z][A-Za-z ]*):(?:\s+.*)?\s*$")
HEADER_HINT_FIELDS = ALLOWED_FIELDS | DISALLOWED_FIELDS
DEFAULT_REPO_DIRS = ("hydra_logger", "scripts", "examples", "tests")
IGNORED_DIRS = {
    ".git",
    ".hydra_env",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "build",
    "dist",
}


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def _changed_python_files(base_ref: str, head_ref: str) -> list[Path]:
    proc = _run_git(
        ["diff", "--name-only", "--diff-filter=AM", f"{base_ref}...{head_ref}"]
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")

    files: list[Path] = []
    for line in proc.stdout.splitlines():
        path = line.strip()
        if not path.endswith(".py"):
            continue
        candidate = Path(path)
        if candidate.exists():
            files.append(candidate)
    return files


def _all_python_files(roots: list[str] | None = None) -> list[Path]:
    if roots:
        scan_roots = [Path(root) for root in roots]
    else:
        scan_roots = [Path(root) for root in DEFAULT_REPO_DIRS]

    files: list[Path] = []
    seen: set[Path] = set()

    for root in scan_roots:
        if root.is_file() and root.suffix == ".py":
            resolved = root.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(root)
            continue

        if not root.exists():
            continue

        for path in root.rglob("*.py"):
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(path)

    for root_file in Path(".").glob("*.py"):
        resolved = root_file.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        files.append(root_file)

    return sorted(files)


def _docstring_fields(docstring: str) -> set[str]:
    fields: set[str] = set()
    for line in docstring.splitlines():
        match = FIELD_PATTERN.match(line)
        if match:
            fields.add(match.group(1).strip())
    return fields


def _extract_docstring(path: Path) -> str | None:
    source = path.read_text(encoding="utf-8")
    module = ast.parse(source)
    return ast.get_docstring(module, clean=False)


def _format_issue(path: Path, message: str) -> str:
    return f"{path.as_posix()}: {message}"


def _analyze_files(files: list[Path]) -> dict[str, Any]:
    findings: dict[str, list[str]] = {
        "parse_errors": [],
        "missing_header": [],
        "disallowed_fields": [],
        "missing_required_fields": [],
        "unknown_fields": [],
    }
    compliant: list[str] = []
    structured = 0

    for path in files:
        try:
            doc = _extract_docstring(path)
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            findings["parse_errors"].append(
                _format_issue(path, f"unable to parse ({exc})")
            )
            continue

        if not doc:
            findings["missing_header"].append(
                _format_issue(path, "missing module docstring header")
            )
            continue

        fields = _docstring_fields(doc)
        if not (fields & HEADER_HINT_FIELDS):
            findings["missing_header"].append(
                _format_issue(
                    path,
                    "module docstring is not structured (missing header fields)",
                )
            )
            continue

        structured += 1
        file_findings = 0

        disallowed = sorted(fields & DISALLOWED_FIELDS)
        if disallowed:
            findings["disallowed_fields"].append(
                _format_issue(
                    path, f"disallowed fields present: {', '.join(disallowed)}"
                )
            )
            file_findings += 1

        missing_required = sorted(REQUIRED_FIELDS - fields)
        if missing_required:
            findings["missing_required_fields"].append(
                _format_issue(
                    path, f"missing required fields: {', '.join(missing_required)}"
                )
            )
            file_findings += 1

        unknown = sorted(fields - ALLOWED_FIELDS - DISALLOWED_FIELDS)
        if unknown:
            findings["unknown_fields"].append(
                _format_issue(path, f"unknown fields present: {', '.join(unknown)}")
            )
            file_findings += 1

        if file_findings == 0:
            compliant.append(path.as_posix())

    total_findings = sum(len(items) for items in findings.values())
    summary: dict[str, Any] = {
        "scanned_files": len(files),
        "structured_headers_detected": structured,
        "compliant_files": len(compliant),
        "total_findings": total_findings,
        "counts": {key: len(value) for key, value in findings.items()},
    }
    return {
        "summary": summary,
        "findings": findings,
        "compliant_files": compliant,
    }


def _write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    findings = report["findings"]
    lines = [
        "# Slim Header Validation Report",
        "",
        "## Summary",
        f"- Scanned files: {summary['scanned_files']}",
        f"- Structured headers detected: {summary['structured_headers_detected']}",
        f"- Compliant files: {summary['compliant_files']}",
        f"- Total findings: {summary['total_findings']}",
        "",
        "## Findings By Category",
    ]
    for category, count in summary["counts"].items():
        lines.append(f"- `{category}`: {count}")

    for category, issues in findings.items():
        if not issues:
            continue
        lines.extend(["", f"## {category}"])
        lines.extend(f"- {issue}" for issue in issues)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _print_report(report: dict[str, Any]) -> None:
    summary = report["summary"]
    findings = report["findings"]

    print(f"Checked Python files: {summary['scanned_files']}")
    print(f"Structured headers detected: {summary['structured_headers_detected']}")
    print(f"Compliant files: {summary['compliant_files']}")
    print(f"Total findings: {summary['total_findings']}")
    print("Category counts:")
    for category, count in summary["counts"].items():
        print(f"- {category}: {count}")

    for category, issues in findings.items():
        if not issues:
            continue
        print(f"\n{category}:")
        for issue in issues:
            print(f"- {issue}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate slim file headers for changed files or full repository."
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base reference for git diff (default: origin/main).",
    )
    parser.add_argument(
        "--head",
        default="HEAD",
        help="Head reference for git diff (default: HEAD).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when findings are found.",
    )
    parser.add_argument(
        "--all-python",
        action="store_true",
        help="Scan all Python files in repository scope (not only changed files).",
    )
    parser.add_argument(
        "--roots",
        nargs="+",
        default=None,
        help="Optional paths to scan in --all-python mode.",
    )
    parser.add_argument(
        "--report-md",
        default="",
        help="Optional path to write a markdown report.",
    )
    parser.add_argument(
        "--report-json",
        default="",
        help="Optional path to write a JSON report.",
    )
    args = parser.parse_args()

    if args.all_python:
        files = _all_python_files(args.roots)
    else:
        try:
            files = _changed_python_files(args.base, args.head)
        except RuntimeError as exc:
            print(f"ERROR: {exc}")
            return 2

    report = _analyze_files(files)
    _print_report(report)

    if args.report_md:
        _write_markdown_report(Path(args.report_md), report)
        print(f"\nWrote markdown report: {args.report_md}")

    if args.report_json:
        json_path = Path(args.report_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote JSON report: {args.report_json}")

    if args.strict and report["summary"]["total_findings"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
