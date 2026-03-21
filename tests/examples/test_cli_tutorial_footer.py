"""
Role: Tests for CLI tutorial run-summary footer helper.
Used By:
 - pytest collection under `tests/examples/`.
Depends On:
 - examples/tutorials/shared/cli_tutorial_footer.py
Notes:
 - Keeps stdout contract stable for onboarding scripts.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TUTORIALS = ROOT / "examples" / "tutorials"
if str(TUTORIALS) not in sys.path:
    sys.path.insert(0, str(TUTORIALS))

from shared.cli_tutorial_footer import print_cli_tutorial_footer  # noqa: E402


def test_print_cli_tutorial_footer_includes_sections(capsys: pytest.CaptureFixture[str]) -> None:
    print_cli_tutorial_footer(
        code="TXX",
        title="Sample",
        console="Nothing special.",
        artifacts=["examples/logs/cli-tutorials/txx.jsonl"],
        extra_lines=["widgets: 3"],
        takeaway="Read the JSONL.",
        notebook_rel="examples/tutorials/notebooks/txx.ipynb",
    )
    out = capsys.readouterr().out
    assert "TXX — Sample" in out
    assert "Console:" in out
    assert "Files:" in out
    assert "examples/logs/cli-tutorials/txx.jsonl" in out
    assert "Details:" in out
    assert "widgets: 3" in out
    assert "Takeaway:" in out
    assert "Notebook:" in out
