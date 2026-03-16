"""
Role: Pytest coverage for rotating handler behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates rotation triggering and factory mapping behavior.
"""

from pathlib import Path

from hydra_logger.handlers import rotating_handler as rotating_module
from hydra_logger.handlers.rotating_handler import (
    HybridRotatingFileHandler,
    RotatingFileHandlerFactory,
    SizeRotatingFileHandler,
    TimedRotatingFileHandler,
)
from hydra_logger.types.enums import TimeUnit
from hydra_logger.types.records import LogRecord


def test_size_rotating_handler_rotates_when_file_exceeds_limit(tmp_path: Path) -> None:
    log_file = tmp_path / "rotating.log"
    handler = SizeRotatingFileHandler(
        filename=str(log_file),
        max_bytes=1,
        backup_count=2,
        buffer_size=1,
        flush_interval=60.0,
    )
    handler.emit(LogRecord(level=20, level_name="INFO", message="first"))
    handler.emit(LogRecord(level=20, level_name="INFO", message="second"))
    handler.close()
    backups = [p for p in tmp_path.iterdir() if p.name.startswith("rotating.")]
    assert backups


def test_rotating_factory_creates_timed_handler_with_mapped_args(tmp_path: Path) -> None:
    handler = RotatingFileHandlerFactory.create_timed_handler(
        filename=str(tmp_path / "time.log"),
        time_interval=1,
        max_time_files=3,
        time_unit=TimeUnit.DAYS,
    )
    assert isinstance(handler, TimedRotatingFileHandler)
    handler.close()


def test_timed_rotating_handler_rejects_invalid_interval(tmp_path: Path) -> None:
    try:
        TimedRotatingFileHandler(
            filename=str(tmp_path / "bad.log"), interval=0, time_unit=TimeUnit.DAYS
        )
    except ValueError as exc:
        assert "Invalid rotation interval" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid timed interval")


def test_rotating_factory_creates_size_and_hybrid_handlers(tmp_path: Path) -> None:
    size_handler = RotatingFileHandlerFactory.create_size_handler(
        filename=str(tmp_path / "size.log"),
        max_size=128,
        max_size_files=2,
    )
    hybrid_handler = RotatingFileHandlerFactory.create_hybrid_handler(
        filename=str(tmp_path / "hybrid.log"),
        max_size=128,
        max_size_files=2,
        time_interval=1,
        max_time_files=2,
    )
    assert isinstance(size_handler, SizeRotatingFileHandler)
    assert isinstance(hybrid_handler, HybridRotatingFileHandler)
    size_handler.close()
    hybrid_handler.close()


def test_rotating_handler_stats_surface_strategy(tmp_path: Path) -> None:
    handler = SizeRotatingFileHandler(
        filename=str(tmp_path / "stats.log"),
        max_bytes=64,
        backup_count=1,
        buffer_size=1,
        flush_interval=1.0,
    )
    stats = handler.get_rotation_stats()
    assert stats["config"]["strategy"] == "size_based"
    handler.close()


def test_size_rotating_handler_logs_size_check_failure(
    monkeypatch, caplog, tmp_path: Path
) -> None:
    handler = SizeRotatingFileHandler(
        filename=str(tmp_path / "size-check.log"),
        max_bytes=64,
        backup_count=1,
    )
    monkeypatch.setattr(
        rotating_module.FileUtility,
        "get_file_info",
        lambda _path: (_ for _ in ()).throw(OSError("boom")),
    )
    # ensure file exists check passes so get_file_info branch is reached
    monkeypatch.setattr(rotating_module.FileUtility, "exists", lambda _path: True)
    # verify method tolerates errors and returns False
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.rotating_handler"):
        assert handler._should_rotate() is False
    assert "Size-based rotation check failed" in caplog.text
    handler.close()
