"""
Role: Isolates factory tests from repository runtime log artifacts.
Used By:
 - Pytest collection under `tests/factories/`.
Depends On:
 - pytest
Notes:
 - Factory defaults can initialize file destinations; run in temp cwd.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_factory_test_cwd(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run factory tests in a per-test temp working directory."""
    monkeypatch.chdir(tmp_path)
