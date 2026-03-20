"""
Role: Tests for PyPI metadata parity script (mocked network).
Used By:
 - pytest / release tooling validation.
Depends On:
 - importlib.util
 - json
 - pathlib
 - unittest.mock
Notes:
 - Avoids live PyPI calls; uses repository canonical version dynamically.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hydra_logger import __version__ as repo_version


def _load_module():
    repo_root = Path(__file__).resolve().parents[3]
    script_path = repo_root / "scripts" / "release" / "check_pypi_parity.py"
    spec = importlib.util.spec_from_file_location(
        f"check_pypi_parity_mod_{uuid.uuid4().hex}", script_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fake_urlopen_factory(payload: dict):
    def _fake_urlopen(*_a, **_k):
        resp = MagicMock()
        resp.read.return_value = json.dumps(payload).encode("utf-8")
        ctx = MagicMock()
        ctx.__enter__.return_value = resp
        ctx.__exit__.return_value = None
        return ctx

    return _fake_urlopen


def test_require_match_passes_when_pypi_matches_repo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_module()
    payload = {
        "info": {
            "version": repo_version,
            "classifiers": [
                "Development Status :: 4 - Beta",
                "Topic :: System :: Logging",
            ],
        }
    }
    monkeypatch.setattr(mod, "urlopen", _fake_urlopen_factory(payload))
    code = mod.main(["--require-match"])
    assert code == 0


def test_require_match_fails_on_version_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_module()
    payload = {
        "info": {
            "version": "0.0.0-fake",
            "classifiers": ["Development Status :: 4 - Beta"],
        }
    }
    monkeypatch.setattr(mod, "urlopen", _fake_urlopen_factory(payload))
    code = mod.main(["--require-match"])
    assert code == 1


def test_require_match_fails_on_classifier_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_module()
    payload = {
        "info": {
            "version": repo_version,
            "classifiers": ["Development Status :: 3 - Alpha"],
        }
    }
    monkeypatch.setattr(mod, "urlopen", _fake_urlopen_factory(payload))
    code = mod.main(["--require-match"])
    assert code == 1


def test_informational_mode_always_zero_on_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_module()
    payload = {"info": {"version": "0.0.0", "classifiers": []}}
    monkeypatch.setattr(mod, "urlopen", _fake_urlopen_factory(payload))
    code = mod.main([])
    assert code == 0
