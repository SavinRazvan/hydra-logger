"""
Role: Enforces release version consistency across governed project files.
Used By:
 - Local maintainers before release commits.
 - CI and PR prepare workflow gates.
Depends On:
 - pathlib
 - re
 - sys
Notes:
 - Uses `hydra_logger.__version__` as canonical release version source.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_FILE = REPO_ROOT / "hydra_logger" / "__init__.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_canonical_version(text: str) -> str:
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if not match:
        raise ValueError("Could not resolve canonical __version__ in hydra_logger/__init__.py")
    return match.group(1)


def _check_contains(path: Path, expected_snippet: str, errors: list[str]) -> None:
    content = _read(path)
    if expected_snippet not in content:
        errors.append(
            f"{path.relative_to(REPO_ROOT)} missing expected snippet: {expected_snippet}"
        )


def _check_contains_any(
    path: Path, expected_snippets: tuple[str, ...], errors: list[str]
) -> None:
    content = _read(path)
    if any(snippet in content for snippet in expected_snippets):
        return
    expected_joined = " OR ".join(expected_snippets)
    errors.append(
        f"{path.relative_to(REPO_ROOT)} missing expected snippet(s): {expected_joined}"
    )


def main() -> int:
    errors: list[str] = []
    canonical_version = _extract_canonical_version(_read(CANONICAL_FILE))

    setup_py = REPO_ROOT / "setup.py"
    _check_contains_any(
        setup_py,
        (
            f'version="{canonical_version}"',
            "version=package_version",
        ),
        errors,
    )

    governed_expectations = [
        (
            REPO_ROOT / "hydra_logger" / "loggers" / "__init__.py",
            f'__version__ = "{canonical_version}"',
        ),
        (
            REPO_ROOT / "hydra_logger" / "extensions" / "base.py",
            f'version: str = "{canonical_version}"',
        ),
        (
            REPO_ROOT / "hydra_logger" / "extensions" / "base.py",
            f'self._version = self.config.get("version", "{canonical_version}")',
        ),
        (
            REPO_ROOT / "tests" / "extensions" / "test_extension_base.py",
            f'assert cfg.version == "{canonical_version}"',
        ),
        (
            REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md",
            f"- **Hydra-Logger Version**: [e.g. {canonical_version}]",
        ),
    ]

    for path, expected in governed_expectations:
        _check_contains(path, expected, errors)

    if errors:
        print("Version consistency check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Version consistency check passed: {canonical_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
