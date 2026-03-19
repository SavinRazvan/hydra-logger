"""
Role: CLI behavior tests for package entrypoint readiness.
Used By:
 - pytest CLI/regression suite.
Depends On:
 - hydra_logger.cli
 - hydra_logger.__version__
Notes:
 - Validates stable CLI output expected by package consumers.
"""

import runpy

import pytest

from hydra_logger import __version__
from hydra_logger.cli import main


def test_cli_version_flag_outputs_package_version(capsys) -> None:
    """CLI should print package version for --version."""
    exit_code = main(["--version"])
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert output == f"hydra-logger {__version__}"


def test_cli_default_message_is_non_error(capsys) -> None:
    """CLI should return success and print guidance without args."""
    exit_code = main([])
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert "Hydra Logger CLI is available." in output


def test_cli_module_main_guard_exits_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    """Importing cli as __main__ should execute SystemExit(main())."""
    monkeypatch.setattr("sys.argv", ["hydra_logger.cli", "--version"])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("hydra_logger.cli", run_name="__main__")
    assert exc_info.value.code == 0
