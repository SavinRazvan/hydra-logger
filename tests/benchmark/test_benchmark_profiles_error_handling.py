"""
Role: Unit tests for benchmark profile error handling paths.
Used By:
 - Pytest benchmark profile validation.
Depends On:
 - benchmark
 - pytest
Notes:
 - Verifies profile loader failures are surfaced with explicit exceptions.
"""

from __future__ import annotations

import pytest

import benchmark.profiles as profiles_mod
from benchmark.profiles import load_profile


def test_load_profile_rejects_unknown_profile() -> None:
    with pytest.raises(ValueError, match="Unknown benchmark profile"):
        load_profile("definitely_missing_profile")


def test_load_profile_rejects_invalid_json(monkeypatch, tmp_path) -> None:
    bad_profile = tmp_path / "bad.json"
    bad_profile.write_text("{ invalid", encoding="utf-8")
    monkeypatch.setattr(profiles_mod, "PROFILE_DIR", tmp_path)

    with pytest.raises(ValueError, match="Invalid benchmark profile JSON"):
        load_profile("bad")


def test_load_profile_rejects_non_object_payload(monkeypatch, tmp_path) -> None:
    list_profile = tmp_path / "list.json"
    list_profile.write_text('["not", "object"]', encoding="utf-8")
    monkeypatch.setattr(profiles_mod, "PROFILE_DIR", tmp_path)

    with pytest.raises(ValueError, match="Invalid profile format"):
        load_profile("list")
