"""
Role: Contract tests for PyPI classifiers declared in setup.py.
Used By:
 - CI to guard packaging stability signals.
Depends On:
 - ast
 - pathlib
Notes:
 - Ensures Development Status reflects the agreed maturity tier.
"""

from __future__ import annotations

import ast
from pathlib import Path


def _classifier_list(setup_path: Path) -> list[str]:
    tree = ast.parse(setup_path.read_text(encoding="utf-8"))
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
            out: list[str] = []
            for elt in kw.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    out.append(elt.value)
            return out
    raise AssertionError("classifiers not found in setup() call")


def test_development_status_is_beta() -> None:
    root = Path(__file__).resolve().parents[2]
    classifiers = _classifier_list(root / "setup.py")
    assert "Development Status :: 4 - Beta" in classifiers
    assert not any("Development Status :: 3 - Alpha" in c for c in classifiers)


def test_development_status_singleton() -> None:
    root = Path(__file__).resolve().parents[2]
    classifiers = _classifier_list(root / "setup.py")
    dev_status = [c for c in classifiers if c.startswith("Development Status ::")]
    assert (
        len(dev_status) == 1
    ), f"expected one Development Status classifier, got {dev_status!r}"
