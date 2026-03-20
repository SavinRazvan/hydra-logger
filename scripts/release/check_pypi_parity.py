"""
Role: Compare repository packaging signals against live PyPI project metadata.
Used By:
 - Maintainers post-publish and optional release preflight (--pypi-parity).
Depends On:
 - argparse
 - ast
 - json
 - pathlib
 - re
 - sys
 - urllib.request
Notes:
 - Network access required; not part of default CI. Use --require-match after upload.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_FILE = REPO_ROOT / "hydra_logger" / "__init__.py"
SETUP_FILE = REPO_ROOT / "setup.py"
PYPI_JSON_TMPL = "https://pypi.org/pypi/{name}/json"
DEFAULT_PACKAGE = "hydra-logger"


def _canonical_repo_version() -> str:
    text = INIT_FILE.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("Could not read __version__ from hydra_logger/__init__.py")
    return match.group(1)


def _repo_development_status_classifier() -> str | None:
    tree = ast.parse(SETUP_FILE.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Expr):
            continue
        call = node.value
        if not isinstance(call, ast.Call):
            continue
        if not isinstance(call.func, ast.Name) or call.func.id != "setup":
            continue
        for kw in call.keywords:
            if kw.arg != "classifiers" or not isinstance(kw.value, ast.List):
                continue
            for elt in kw.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    if elt.value.startswith("Development Status ::"):
                        return elt.value
    return None


def _fetch_pypi_info(package: str) -> dict:
    url = PYPI_JSON_TMPL.format(name=package)
    with urlopen(url, timeout=30) as resp:  # nosec B310 — intentional PyPI index probe
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare hydra-logger repo version/classifiers to PyPI metadata."
    )
    parser.add_argument(
        "--require-match",
        action="store_true",
        help="Exit non-zero when PyPI version or Development Status diverges from repo.",
    )
    parser.add_argument(
        "--package",
        default=DEFAULT_PACKAGE,
        help="PyPI project name (default: hydra-logger).",
    )
    args = parser.parse_args(argv)

    repo_version = _canonical_repo_version()
    repo_status = _repo_development_status_classifier()

    try:
        payload = _fetch_pypi_info(args.package)
    except URLError as exc:
        print(f"PyPI request failed: {exc}", file=sys.stderr)
        return 2

    info = payload.get("info") or {}
    pypi_version = str(info.get("version", ""))
    classifiers = info.get("classifiers") or []
    pypi_status = next(
        (
            c
            for c in classifiers
            if isinstance(c, str) and c.startswith("Development Status ::")
        ),
        None,
    )

    print(f"repo_version={repo_version}")
    print(f"pypi_version={pypi_version}")
    print(f"repo_development_status={repo_status!r}")
    print(f"pypi_development_status={pypi_status!r}")

    if not args.require_match:
        return 0

    mismatches: list[str] = []
    if pypi_version != repo_version:
        mismatches.append(
            f"version mismatch: repository={repo_version!r} pypi={pypi_version!r}"
        )
    if repo_status and pypi_status != repo_status:
        mismatches.append(
            f"Development Status mismatch: repository={repo_status!r} pypi={pypi_status!r}"
        )

    if mismatches:
        print("PyPI parity check failed:", file=sys.stderr)
        for line in mismatches:
            print(f"- {line}", file=sys.stderr)
        return 1

    print("PyPI parity check passed (versions and Development Status align).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
