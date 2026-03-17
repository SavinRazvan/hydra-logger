"""
Role: Isolates logger tests from repository runtime log artifacts.
Used By:
 - Pytest collection under `tests/loggers/`.
Depends On:
 - pytest
Notes:
 - Forces each logger test to run from a temporary working directory.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_logger_test_cwd(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run logger tests in a per-test temp working directory."""
    monkeypatch.chdir(tmp_path)
