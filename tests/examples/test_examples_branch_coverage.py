"""
Role: Pytest branch coverage for examples and tutorial runtime scripts.
Used By:
 - Pytest discovery and CI quality gates.
Depends On:
 - asyncio
 - builtins
 - importlib.util
 - pathlib
 - runpy
 - subprocess
Notes:
 - Covers edge branches that are not exercised by happy-path runtime execution tests.
"""

from __future__ import annotations

import asyncio
import builtins
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


def test_example_04_covers_extension_manager_failure_paths(monkeypatch, capsys) -> None:
    from hydra_logger.extensions import ExtensionManager

    def _raise_init(
        self, *args: Any, **kwargs: Any
    ) -> None:  # pragma: no cover - runtime hook
        raise RuntimeError("forced extension manager failure")

    monkeypatch.setattr(ExtensionManager, "__init__", _raise_init)
    runpy.run_path(
        str(ROOT / "examples" / "04_runtime_control.py"), run_name="__main__"
    )
    output = capsys.readouterr().out
    assert "ExtensionManager example - this may require additional setup" in output


@pytest.mark.parametrize(
    "script_name",
    ["06_basic_colored_logging.py", "11_quick_start_basic.py"],
)
def test_examples_cover_import_error_guidance(
    script_name: str, monkeypatch, capsys
) -> None:
    real_import = builtins.__import__

    def _import_with_forced_failure(
        name: str,
        globals_dict: dict[str, Any] | None = None,
        locals_dict: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ):
        if name == "hydra_logger":
            raise ImportError("forced missing package")
        return real_import(name, globals_dict, locals_dict, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _import_with_forced_failure)
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(ROOT / "examples" / script_name), run_name="__main__")
    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "hydra_logger package not found" in output


def test_example_15_covers_graceful_shutdown_mixin_paths() -> None:
    module = _load_module(
        ROOT / "examples" / "15_eda_microservices_patterns.py", "example15_branch_cov"
    )

    class _DummyLogger:
        def info(self, message: str, **kwargs: Any) -> None:
            _ = (message, kwargs)

        def error(self, message: str, **kwargs: Any) -> None:
            _ = (message, kwargs)

    class _Service(module.GracefulShutdownMixin):
        def __init__(self) -> None:
            super().__init__()
            self.logger = _DummyLogger()

    async def _async_handler() -> None:
        return None

    def _sync_handler() -> None:
        return None

    def _failing_handler() -> None:
        raise RuntimeError("forced handler failure")

    service = _Service()
    service.register_shutdown_handler(_async_handler)
    service.register_shutdown_handler(_sync_handler)
    service.register_shutdown_handler(_failing_handler)
    asyncio.run(service.shutdown())


def test_example_15_main_covers_cancelled_error_branch(monkeypatch) -> None:
    module = _load_module(
        ROOT / "examples" / "15_eda_microservices_patterns.py", "example15_cancel_cov"
    )

    async def _slow_start(self) -> None:
        await asyncio.sleep(1)

    monkeypatch.setattr(module.MicroserviceApp, "start", _slow_start)
    asyncio.run(module.main())


def test_example_16_covers_optional_query_id_and_auth_failure(monkeypatch) -> None:
    module = _load_module(
        ROOT / "examples" / "16_multi_layer_web_app.py", "example16_branch_cov"
    )

    class _AsyncLogger:
        async def info(self, message: str, **kwargs: Any) -> None:
            _ = (message, kwargs)

        async def debug(self, message: str, **kwargs: Any) -> None:
            _ = (message, kwargs)

        async def warning(self, message: str, **kwargs: Any) -> None:
            _ = (message, kwargs)

    app = module.WebApplication(_AsyncLogger())
    monkeypatch.setattr(module.random, "random", lambda: 0.0)
    asyncio.run(app.query_database("SELECT", "users"))
    success = asyncio.run(app.authenticate_user("user-1", "password"))
    assert success is False


def test_run_all_examples_branch_paths(monkeypatch, tmp_path: Path, capsys) -> None:
    module = _load_module(
        ROOT / "examples" / "run_all_examples.py", "run_all_examples_branch_cov"
    )

    # colorize tty path
    monkeypatch.setattr(module.sys.stdout, "isatty", lambda: True)
    assert module.Colors.GREEN in module.colorize("ok", module.Colors.GREEN)

    # run_example timeout path
    def _raise_timeout(*args: Any, **kwargs: Any):
        raise subprocess.TimeoutExpired(cmd="python script.py", timeout=30)

    monkeypatch.setattr(module.subprocess, "run", _raise_timeout)
    success, _stdout, stderr, _duration, _meta = module.run_example(Path("example.py"))
    assert success is False
    assert "Timeout after 30 seconds" in stderr

    # run_example generic exception path
    def _raise_generic(*args: Any, **kwargs: Any):
        raise RuntimeError("forced subprocess failure")

    monkeypatch.setattr(module.subprocess, "run", _raise_generic)
    success, _stdout, stderr, _duration, _meta = module.run_example(Path("example.py"))
    assert success is False
    assert "forced subprocess failure" in stderr

    # verify log discovery paths
    logs_dir = tmp_path / "logs" / "examples"
    logs_dir.mkdir(parents=True)
    (logs_dir / "01_format_control.log").write_text("x", encoding="utf-8")
    (logs_dir / "01_other.jsonl").write_text("x", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    found, patterns = module.verify_log_files("01_format_control.py")
    assert "01_format_control.log" in found
    assert patterns

    # format_duration >= 1s branch
    assert module.format_duration(1.5).endswith("s")

    # print_header coverage
    module.print_header()
    header_output = capsys.readouterr().out
    assert "Hydra-Logger Examples Test Runner" in header_output

    # print_example_result branches
    module.print_example_result(
        "example.py",
        True,
        "Example completed",
        "",
        0.2,
        {},
        [],
    )
    ok_output = capsys.readouterr().out
    assert "No log files detected" in ok_output
    module.print_example_result(
        "example.py",
        True,
        "Example completed",
        "",
        0.2,
        {},
        ["example.log"],
    )
    logs_output = capsys.readouterr().out
    assert "Log files:" in logs_output

    # print_summary both success and failure report paths
    module.print_summary([("ok.py", True, 0.2, ["ok.log"])], 0.2)
    success_output = capsys.readouterr().out
    assert "All examples executed successfully!" in success_output
    module.print_summary([("bad.py", False, 0.2, [])], 0.2)
    fail_output = capsys.readouterr().out
    assert "Failed Examples:" in fail_output


def test_run_all_examples_main_paths(monkeypatch, tmp_path: Path) -> None:
    module = _load_module(
        ROOT / "examples" / "run_all_examples.py", "run_all_examples_main_cov"
    )

    # No example files branch
    no_examples_dir = tmp_path / "empty"
    no_examples_dir.mkdir()
    fake_entry = no_examples_dir / "run_all_examples.py"
    fake_entry.write_text("# fake", encoding="utf-8")
    monkeypatch.setattr(module, "__file__", str(fake_entry))
    assert module.main() == 1

    # Normal main flow with async example branch and failure summary branch
    full_dir = tmp_path / "full"
    full_dir.mkdir()
    full_entry = full_dir / "run_all_examples.py"
    full_entry.write_text("# fake", encoding="utf-8")
    for file_name in ("12_quick_start_async.py", "11_quick_start_basic.py"):
        (full_dir / file_name).write_text("print('ok')", encoding="utf-8")

    monkeypatch.setattr(module, "__file__", str(full_entry))
    monkeypatch.setattr(
        module,
        "run_example",
        lambda f: (
            False if "11_" in f.name else True,
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
