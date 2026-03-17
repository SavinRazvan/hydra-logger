"""
Role: Isolates core logger-management tests from repository log artifacts.
Used By:
 - Pytest collection under `tests/core/`.
Depends On:
 - pytest
Notes:
 - Core manager tests can instantiate default loggers with file destinations.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_core_test_cwd(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run core tests in a per-test temp working directory."""
    monkeypatch.chdir(tmp_path)
