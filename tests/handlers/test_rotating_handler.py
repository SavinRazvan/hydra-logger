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
from datetime import datetime, timedelta
from types import SimpleNamespace

from hydra_logger.handlers import rotating_handler as rotating_module
from hydra_logger.handlers.rotating_handler import (
    RotationConfig,
    RotationStrategy,
    RotatingFileHandler,
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


class _TestRotatingHandler(RotatingFileHandler):
    def __init__(self, filename: str, should_rotate: bool = False, **kwargs):
        self._rotate_flag = should_rotate
        super().__init__(filename=filename, **kwargs)

    def _should_rotate(self) -> bool:
        return self._rotate_flag


def test_rotating_handler_atomic_rotate_and_backup_path(tmp_path: Path) -> None:
    log_file = tmp_path / "atomic.log"
    log_file.write_text("data", encoding="utf-8")
    handler = _TestRotatingHandler(str(log_file))
    backup_path = str(tmp_path / "atomic.1.log")
    handler._atomic_rotate(backup_path)
    assert Path(backup_path).exists()
    handler.close()


def test_rotating_handler_generate_backup_name_without_extension(tmp_path: Path) -> None:
    config = RotationConfig(preserve_extension=False)
    handler = _TestRotatingHandler(str(tmp_path / "base.log"), config=config)
    name = handler._generate_backup_name()
    assert name.startswith("base.")
    assert not name.endswith(".log")
    handler.close()


def test_rotating_handler_compress_file_error_logs_warning(
    monkeypatch, caplog, tmp_path: Path
) -> None:
    target = tmp_path / "compress.log"
    target.write_text("x", encoding="utf-8")
    handler = _TestRotatingHandler(str(tmp_path / "base2.log"))
    monkeypatch.setattr(rotating_module.gzip, "open", lambda *_a, **_k: (_ for _ in ()).throw(OSError("gzip fail")))
    with caplog.at_level("WARNING", logger="hydra_logger.handlers.rotating_handler"):
        handler._compress_file(str(target))
    assert "Failed to compress rotated file" in caplog.text
    handler.close()


def test_rotating_handler_cleanup_old_files_prunes_excess(monkeypatch, tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    for idx in range(4):
        file = backup_dir / f"cleanup.log.{idx}"
        file.write_text("x", encoding="utf-8")

    config = RotationConfig(
        strategy=RotationStrategy.SIZE_BASED,
        max_size_files=2,
        backup_dir=str(backup_dir),
        cleanup_old=True,
    )
    handler = _TestRotatingHandler(str(tmp_path / "cleanup.log"), config=config)
    monkeypatch.setattr(rotating_module.FileUtility, "is_file", lambda _p: True)
    monkeypatch.setattr(
        rotating_module.FileUtility,
        "get_file_info",
        lambda p: SimpleNamespace(mtime=len(str(p))),
    )
    deleted = []
    monkeypatch.setattr(rotating_module.FileUtility, "delete_file", lambda p: deleted.append(p))
    handler._cleanup_old_files()
    assert len(deleted) >= 2
    handler.close()


def test_rotating_handler_cleanup_old_files_delete_failure_logs(
    monkeypatch, caplog, tmp_path: Path
) -> None:
    backup_dir = tmp_path / "warn-backups"
    backup_dir.mkdir()
    p = backup_dir / "warn.log.1"
    p.write_text("x", encoding="utf-8")
    config = RotationConfig(backup_dir=str(backup_dir), cleanup_old=True, max_time_files=0)
    handler = _TestRotatingHandler(str(tmp_path / "warn.log"), config=config)
    monkeypatch.setattr(rotating_module.FileUtility, "is_file", lambda _p: True)
    monkeypatch.setattr(
        rotating_module.FileUtility,
        "get_file_info",
        lambda p: SimpleNamespace(mtime=len(str(p))),
    )
    monkeypatch.setattr(
        rotating_module.FileUtility,
        "delete_file",
        lambda _p: (_ for _ in ()).throw(OSError("cannot delete")),
    )
    with caplog.at_level("WARNING", logger="hydra_logger.handlers.rotating_handler"):
        handler._cleanup_old_files()
    assert "Failed to delete old rotated file" in caplog.text
    handler.close()


def test_rotating_handler_write_to_file_header_footer_paths(tmp_path: Path) -> None:
    class HeaderFormatter:
        def __init__(self) -> None:
            self._marked = False

        def reset_for_new_file(self):
            return None

        def set_file_id(self, _fid):
            return None

        def write_header(self):
            return "["

        def write_footer(self):
            return "]"

    path = tmp_path / "headers.log"
    handler = _TestRotatingHandler(str(path))
    handler.setFormatter(HeaderFormatter())
    handler._write_to_file("entry")
    content = path.read_text(encoding="utf-8")
    assert "[" in content
    assert "entry" in content
    handler.close()


def test_rotating_handler_set_formatter_corrects_filename(tmp_path: Path) -> None:
    class ValidatingFormatter:
        def validate_filename(self, filename: str) -> str:
            return filename + ".jsonl"

        def format(self, record) -> str:
            return record.message

    handler = _TestRotatingHandler(str(tmp_path / "base-name.log"))
    handler.setFormatter(ValidatingFormatter())
    assert handler._filename.endswith(".jsonl")
    handler.close()


def test_timed_rotating_handler_should_rotate_for_all_modes(tmp_path: Path) -> None:
    path = tmp_path / "timed.log"
    for when in ("second", "minute", "midnight", "hour", "day", "week", "month"):
        handler = TimedRotatingFileHandler(filename=str(path), when=when, interval=1)
        if when == "midnight":
            handler._last_rotation_time = datetime.now() - timedelta(days=1)
        elif when == "month":
            handler._last_rotation_time = datetime.now() - timedelta(days=31)
        elif when == "week":
            handler._last_rotation_time = datetime.now() - timedelta(days=8)
        elif when == "day":
            handler._last_rotation_time = datetime.now() - timedelta(days=2)
        elif when == "hour":
            handler._last_rotation_time = datetime.now() - timedelta(hours=2)
        elif when == "minute":
            handler._last_rotation_time = datetime.now() - timedelta(minutes=2)
        else:
            handler._last_rotation_time = datetime.now() - timedelta(seconds=2)
        assert handler._should_rotate() is True
        handler.close()


def test_hybrid_rotating_handler_size_and_time_branches(
    monkeypatch, tmp_path: Path
) -> None:
    path = tmp_path / "hybrid-branch.log"
    handler = HybridRotatingFileHandler(filename=str(path), max_bytes=10, when="day", interval=1)

    monkeypatch.setattr(rotating_module.FileUtility, "exists", lambda _p: True)
    monkeypatch.setattr(
        rotating_module.FileUtility,
        "get_file_info",
        lambda _p: SimpleNamespace(size=100),
    )
    assert handler._should_rotate() is True

    monkeypatch.setattr(
        rotating_module.FileUtility,
        "get_file_info",
        lambda _p: (_ for _ in ()).throw(OSError("size fail")),
    )
    handler._last_rotation_time = datetime.now() - timedelta(days=2)
    assert handler._should_rotate() is True
    handler.close()


def test_rotating_factory_create_handler_unknown_type_raises(tmp_path: Path) -> None:
    try:
        RotatingFileHandlerFactory.create_handler("unknown", filename=str(tmp_path / "x.log"))
    except ValueError as exc:
        assert "Unknown handler type" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown rotating handler type")
