"""
Role: Pytest coverage for test check env health behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - importlib
 - pathlib
 - sys
Notes:
 - Validates test check env health behavior, edge cases, and regression safety.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_check_env_health_module():
    repo_root = Path(__file__).resolve().parents[3]
    script_path = repo_root / "scripts" / "dev" / "check_env_health.py"
    spec = importlib.util.spec_from_file_location("check_env_health", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_check_pip_health_warns_on_dependency_mismatches(monkeypatch) -> None:
    module = _load_check_env_health_module()
    responses = iter(
        [
            (0, "pip 26.0.1 from /tmp/site-packages/pip"),
            (1, "sample-package 1.0 requires other-package>=2.0, which is not installed."),
        ]
    )
    monkeypatch.setattr(module, "_run", lambda cmd, env=None: next(responses))

    result = module._check_pip_health(Path("/tmp/python"))

    assert result.status == module.STATUS_WARN
    assert result.check_id == "pip_health"


def test_check_pip_health_fails_when_pip_crashes(monkeypatch) -> None:
    module = _load_check_env_health_module()
    crash_output = (
        "Traceback (most recent call last):\n"
        "  ...\n"
        "ModuleNotFoundError: No module named 'pip._internal.operations.build'"
    )
    responses = iter(
        [
            (0, "pip 26.0.1 from /tmp/site-packages/pip"),
            (1, crash_output),
        ]
    )
    monkeypatch.setattr(module, "_run", lambda cmd, env=None: next(responses))

    result = module._check_pip_health(Path("/tmp/python"))

    assert result.status == module.STATUS_WARN
    assert "pip check" in result.recommended_fix
