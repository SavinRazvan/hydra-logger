"""
Role: Packaging metadata contract tests for optional dependency hygiene.
Used By:
 - CI and maintainers validating `setup.py` extras layout.
Depends On:
 - ast, pathlib
Notes:
 - Keeps `dev` free of PyUp `safety` (transitive `nltk` tripped pip-audit with no fix on PyPI).
"""

from __future__ import annotations

import ast
from pathlib import Path


def _extras_require_dict(setup_path: Path) -> dict[str, list[str]]:
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
            if kw.arg == "extras_require" and isinstance(kw.value, ast.Dict):
                out: dict[str, list[str]] = {}
                for key_node, val_node in zip(
                    kw.value.keys, kw.value.values, strict=False
                ):
                    if key_node is None or val_node is None:
                        continue
                    if not isinstance(key_node, ast.Constant) or not isinstance(
                        key_node.value, str
                    ):
                        continue
                    if not isinstance(val_node, ast.List):
                        continue
                    reqs: list[str] = []
                    for elt in val_node.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            reqs.append(elt.value)
                    out[key_node.value] = reqs
                return out
    raise AssertionError("extras_require not found in setup() call")


def test_dev_extra_excludes_safety_package() -> None:
    root = Path(__file__).resolve().parents[2]
    extras = _extras_require_dict(root / "setup.py")
    dev = extras.get("dev", [])
    assert not any(r.strip().lower().startswith("safety") for r in dev), (
        "dev extra must not depend on safety (transitive nltk breaks pip-audit); "
        "use optional extra legacy_safety instead."
    )


def test_legacy_safety_extra_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    extras = _extras_require_dict(root / "setup.py")
    assert "legacy_safety" in extras
    assert any(r.strip().lower().startswith("safety") for r in extras["legacy_safety"])
