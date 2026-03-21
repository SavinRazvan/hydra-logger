"""
Role: Pytest branch coverage for tutorial runtime scripts.
Used By:
 - Pytest discovery and CI quality gates.
Depends On:
 - importlib.util
 - pathlib
 - runpy
 - subprocess
Notes:
 - Covers runner edge branches and canonical tutorial-path execution behavior.
"""

from __future__ import annotations

import importlib.util
import runpy
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_t15_tutorial_executes_under_main(monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    runpy.run_path(
        str(
            ROOT
            / "examples"
            / "tutorials"
            / "cli_tutorials"
            / "t15_enterprise_network_hardening_playbook.py"
        ),
        run_name="__main__",
    )


def test_run_all_examples_branch_paths(monkeypatch, tmp_path: Path, capsys) -> None:
    module = _load_module(
        ROOT / "examples" / "run_all_examples.py", "run_all_examples_branch_cov"
    )

    monkeypatch.setattr(module.sys.stdout, "isatty", lambda: True)
    assert module.Colors.GREEN in module.colorize("ok", module.Colors.GREEN)

    def _raise_timeout(*args: Any, **kwargs: Any):
        raise subprocess.TimeoutExpired(cmd="python script.py", timeout=30)

    monkeypatch.setattr(module.subprocess, "run", _raise_timeout)
    success, _stdout, stderr, _duration, _meta = module.run_example(Path("example.py"))
    assert success is False
    assert "Timeout after 30 seconds" in stderr

    def _raise_generic(*args: Any, **kwargs: Any):
        raise RuntimeError("forced subprocess failure")

    monkeypatch.setattr(module.subprocess, "run", _raise_generic)
    success, _stdout, stderr, _duration, _meta = module.run_example(Path("example.py"))
    assert success is False
    assert "forced subprocess failure" in stderr

    logs_dir = tmp_path / "examples" / "logs" / "cli-tutorials"
    logs_dir.mkdir(parents=True)
    (logs_dir / "t01_production_quick_start.log").write_text("x", encoding="utf-8")
    (logs_dir / "t01_other.jsonl").write_text("x", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    found, patterns = module.verify_log_files("t01_production_quick_start.py")
    assert "t01_production_quick_start.log" in found
    assert patterns

    assert module.format_duration(1.5).endswith("s")

    module.print_header()
    header_output = capsys.readouterr().out
    assert "Hydra-Logger Tutorials Test Runner" in header_output

    module.print_example_result(
        "tutorial.py",
        True,
        "Tutorial completed",
        "",
        0.2,
        {},
        [],
    )
    ok_output = capsys.readouterr().out
    assert "No log files detected" in ok_output

    module.print_summary([("ok.py", True, 0.2, ["ok.log"])], 0.2)
    success_output = capsys.readouterr().out
    assert "All tutorials executed successfully!" in success_output

    module.print_summary([("bad.py", False, 0.2, [])], 0.2)
    fail_output = capsys.readouterr().out
    assert "Failed Tutorials:" in fail_output


def test_run_all_examples_main_paths(monkeypatch, tmp_path: Path) -> None:
    module = _load_module(
        ROOT / "examples" / "run_all_examples.py", "run_all_examples_main_cov"
    )

    no_examples_dir = tmp_path / "empty"
    no_examples_dir.mkdir(parents=True)
    fake_entry = no_examples_dir / "run_all_examples.py"
    fake_entry.write_text("# fake", encoding="utf-8")
    monkeypatch.setattr(module, "__file__", str(fake_entry))
    assert module.main() == 1

    full_dir = tmp_path / "full"
    (full_dir / "tutorials" / "cli_tutorials").mkdir(parents=True)
    full_entry = full_dir / "run_all_examples.py"
    full_entry.write_text("# fake", encoding="utf-8")
    for file_name in ("t02_configuration_recipes.py", "t03_layers_customization.py"):
        (full_dir / "tutorials" / "cli_tutorials" / file_name).write_text(
            "print('ok')", encoding="utf-8"
        )

    monkeypatch.setattr(module, "__file__", str(full_entry))
    monkeypatch.setattr(
        module,
        "run_example",
        lambda f: (
            False if "t03_" in f.name else True,
            "completed",
            "",
            0.01,
            {"example": f.name},
        ),
    )
    monkeypatch.setattr(module, "verify_log_files", lambda _name: ([], []))
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    assert module.main() == 1


def test_run_all_examples_dunder_main_executes(tmp_path: Path) -> None:
    source = (ROOT / "examples" / "run_all_examples.py").read_text(encoding="utf-8")
    copied = tmp_path / "run_all_examples.py"
    copied.write_text(source, encoding="utf-8")
    with pytest.raises(SystemExit):
        runpy.run_path(str(copied), run_name="__main__")


def test_run_all_examples_original_dunder_main_executes() -> None:
    with pytest.raises(SystemExit):
        runpy.run_path(
            str(ROOT / "examples" / "run_all_examples.py"), run_name="__main__"
        )
