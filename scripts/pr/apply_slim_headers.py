"""
Role: Apply slim module headers across Python code files.
Used By:
 - maintainers running repository-wide header migration
Depends On:
 - argparse
 - ast
 - pathlib
 - subprocess
Notes:
 - Rewrites module docstrings to the slim header format.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path
from typing import Any

FIELD_NAMES = ("Role", "Used By", "Depends On", "Notes")
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
    proc = _run_git(["diff", "--name-only", "--diff-filter=AM", f"{base_ref}...{head_ref}"])
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
    return sorted(files)


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


def _parse_field_map(docstring: str) -> dict[str, Any]:
    field_map: dict[str, Any] = {
        "Role": "",
        "Used By": [],
        "Depends On": [],
        "Notes": [],
    }
    current_field = ""

    for raw_line in docstring.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue

        matched_field = ""
        for field in FIELD_NAMES:
            if stripped.startswith(f"{field}:"):
                matched_field = field
                break

        if matched_field:
            current_field = matched_field
            inline_value = stripped.split(":", 1)[1].strip()
            if matched_field == "Role":
                if inline_value:
                    field_map["Role"] = inline_value
            elif inline_value:
                field_map[matched_field].append(inline_value.lstrip("- ").strip())
            continue

        if stripped.startswith("-") and current_field in ("Used By", "Depends On", "Notes"):
            field_map[current_field].append(stripped.lstrip("- ").strip())

    return field_map


def _default_role(path: Path) -> str:
    slug = path.stem.replace("_", " ").strip()
    if not slug:
        slug = "module"
    return f"{slug.capitalize()} implementation."


def _default_depends(module: ast.Module) -> list[str]:
    deps: list[str] = []
    seen: set[str] = set()

    for node in module.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".", 1)[0]
                if name not in seen:
                    seen.add(name)
                    deps.append(name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                name = node.module.split(".", 1)[0]
                if name not in seen:
                    seen.add(name)
                    deps.append(name)

    if not deps:
        return ["(none)"]
    return deps[:5]


def _build_header(path: Path, module: ast.Module, existing_docstring: str | None) -> str:
    parsed = _parse_field_map(existing_docstring or "")
    role = parsed["Role"] or _default_role(path)
    used_by = parsed["Used By"] or ["(update when known)"]
    depends = parsed["Depends On"] or _default_depends(module)
    notes = parsed["Notes"] or ["Header standardized by slim-header migration."]

    lines = [
        '"""',
        f"Role: {role}",
        "Used By:",
    ]
    lines.extend([f" - {item}" for item in used_by])
    lines.append("Depends On:")
    lines.extend([f" - {item}" for item in depends])
    lines.append("Notes:")
    lines.extend([f" - {item}" for item in notes])
    lines.append('"""')
    return "\n".join(lines)


def _docstring_span(module: ast.Module) -> tuple[int, int] | None:
    if not module.body:
        return None
    node = module.body[0]
    if not isinstance(node, ast.Expr):
        return None
    if not isinstance(node.value, ast.Constant):
        return None
    if not isinstance(node.value.value, str):
        return None
    if node.lineno is None or node.end_lineno is None:
        return None
    return node.lineno, node.end_lineno


def _insertion_index(lines: list[str]) -> int:
    idx = 0
    if lines and lines[0].startswith("#!"):
        idx = 1
    if idx < len(lines) and "coding" in lines[idx]:
        idx += 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    return idx


def _rewrite_file(path: Path, dry_run: bool) -> tuple[bool, str]:
    source = path.read_text(encoding="utf-8")
    try:
        module = ast.parse(source)
    except SyntaxError as exc:
        return False, f"syntax error: {exc}"

    existing_docstring = ast.get_docstring(module, clean=False)
    new_docstring = _build_header(path, module, existing_docstring)
    source_lines = source.splitlines()
    span = _docstring_span(module)

    if span:
        start_line, end_line = span
        replaced_lines = source_lines[: start_line - 1] + [new_docstring] + source_lines[end_line:]
    else:
        insert_at = _insertion_index(source_lines)
        prefix = source_lines[:insert_at]
        suffix = source_lines[insert_at:]
        block = [new_docstring, ""]
        replaced_lines = prefix + block + suffix

    new_source = "\n".join(replaced_lines) + "\n"
    if new_source == source:
        return False, "already compliant"

    if not dry_run:
        path.write_text(new_source, encoding="utf-8")
    return True, "updated"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply slim headers to changed files or repository-wide Python files."
    )
    parser.add_argument("--base", default="origin/main", help="Base ref for changed-file mode.")
    parser.add_argument("--head", default="HEAD", help="Head ref for changed-file mode.")
    parser.add_argument(
        "--all-python",
        action="store_true",
        help="Apply changes to all Python files in repository scope.",
    )
    parser.add_argument(
        "--roots",
        nargs="+",
        default=None,
        help="Optional paths to scan in --all-python mode.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without writing files.",
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

    changed = 0
    skipped = 0
    errors = 0

    for path in files:
        try:
            did_change, note = _rewrite_file(path, dry_run=args.dry_run)
        except OSError as exc:
            errors += 1
            print(f"ERROR {path.as_posix()}: {exc}")
            continue

        if did_change:
            changed += 1
            print(f"UPDATED {path.as_posix()}: {note}")
        else:
            skipped += 1
            print(f"SKIP {path.as_posix()}: {note}")

    print(
        f"\nSlim header migration summary -> scanned={len(files)} changed={changed} skipped={skipped} errors={errors}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
