"""
Role: Pytest coverage for rotating handler behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates rotation triggering and factory mapping behavior.
"""

from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from hydra_logger.handlers import rotating_handler as rotating_module
from hydra_logger.handlers.rotating_handler import (
    HybridRotatingFileHandler,
    RotatingFileHandler,
    RotatingFileHandlerFactory,
    RotationConfig,
    RotationStrategy,
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


def test_rotating_factory_creates_timed_handler_with_mapped_args(
    tmp_path: Path,
) -> None:
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


def test_rotating_handler_generate_backup_name_without_extension(
    tmp_path: Path,
) -> None:
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
    monkeypatch.setattr(
        rotating_module.gzip,
        "open",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("gzip fail")),
    )
    with caplog.at_level("WARNING", logger="hydra_logger.handlers.rotating_handler"):
        handler._compress_file(str(target))
    assert "Failed to compress rotated file" in caplog.text
    handler.close()


def test_rotating_handler_cleanup_old_files_prunes_excess(
    monkeypatch, tmp_path: Path
) -> None:
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
    monkeypatch.setattr(
        rotating_module.FileUtility, "delete_file", lambda p: deleted.append(p)
    )
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
    config = RotationConfig(
        backup_dir=str(backup_dir), cleanup_old=True, max_time_files=0
    )
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
    handler = HybridRotatingFileHandler(
        filename=str(path), max_bytes=10, when="day", interval=1
    )

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
        RotatingFileHandlerFactory.create_handler(
            "unknown", filename=str(tmp_path / "x.log")
        )
    except ValueError as exc:
        assert "Unknown handler type" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown rotating handler type")


def test_rotating_base_should_rotate_raises_not_implemented(tmp_path: Path) -> None:
    handler = _TestRotatingHandler(str(tmp_path / "base-raise.log"))
    with pytest.raises(NotImplementedError):
        RotatingFileHandler._should_rotate(handler)
    handler.close()


def test_rotating_handler_init_and_initialize_error_paths(
    monkeypatch, tmp_path: Path
) -> None:
    seen = {"ensured": False}
    original_exists = rotating_module.FileUtility.exists

    def _exists(path: str) -> bool:
        if str(path) == str(tmp_path / "new-dir"):
            return False
        return original_exists(path)

    monkeypatch.setattr(rotating_module.FileUtility, "exists", _exists)
    monkeypatch.setattr(
        rotating_module.FileUtility,
        "ensure_directory_exists",
        lambda p: (
            Path(p).mkdir(parents=True, exist_ok=True),
            seen.__setitem__("ensured", True),
        ),
    )
    monkeypatch.setattr(rotating_module.FileUtility, "is_writable", lambda _path: False)

    with pytest.raises(PermissionError):
        _TestRotatingHandler(str(tmp_path / "new-dir" / "bad.log"))
    assert seen["ensured"] is True


def test_rotating_handler_rotate_paths_and_recovery(
    monkeypatch, caplog, tmp_path: Path
) -> None:
    log_file = tmp_path / "rotate-main.log"
    log_file.write_text("a", encoding="utf-8")
    config = RotationConfig(
        atomic_rotation=False, compress_old=False, cleanup_old=False
    )
    handler = _TestRotatingHandler(str(log_file), should_rotate=False, config=config)
    # Early return when rotation is not needed.
    handler._rotate_file()

    moved = {"count": 0}
    monkeypatch.setattr(
        rotating_module.shutil,
        "move",
        lambda src, dst: moved.__setitem__("count", moved["count"] + 1)
        or Path(dst).write_text("x", encoding="utf-8"),
    )
    handler._rotate_flag = True
    handler._rotate_file()
    assert moved["count"] >= 1

    # Error + recovery-reopen failure path.
    monkeypatch.setattr(
        handler,
        "_generate_backup_name",
        lambda: (_ for _ in ()).throw(RuntimeError("rotate fail")),
    )
    monkeypatch.setattr(
        handler,
        "_initialize_file",
        lambda: (_ for _ in ()).throw(RuntimeError("reopen fail")),
    )
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.rotating_handler"):
        handler._rotate_file()
    assert "Rotating file operation failed" in caplog.text
    assert "Rotating file recovery reopen failed" in caplog.text
    handler.close()


def test_rotating_atomic_backup_name_and_backup_dir_paths(tmp_path: Path) -> None:
    path = tmp_path / "atomic-main.log"
    path.write_text("payload", encoding="utf-8")
    backup_path = tmp_path / "atomic-main.1.log"
    backup_path.write_text("old", encoding="utf-8")
    handler = _TestRotatingHandler(str(path))
    handler._atomic_rotate(str(backup_path))
    assert backup_path.exists()

    preserved = handler._generate_backup_name()
    assert preserved.endswith(".log")

    with_backup_dir = _TestRotatingHandler(
        str(tmp_path / "with-dir.log"),
        config=RotationConfig(backup_dir=str(tmp_path / "bk")),
    )
    backup_target = with_backup_dir._get_backup_path("x.log")
    assert backup_target.startswith(str(tmp_path / "bk"))
    handler.close()
    with_backup_dir.close()


def test_rotating_cleanup_hybrid_missing_dir_and_delete_failure(
    monkeypatch, caplog, tmp_path: Path
) -> None:
    missing_dir = _TestRotatingHandler(
        str(tmp_path / "missing.log"),
        config=RotationConfig(
            backup_dir=str(tmp_path / "does-not-exist"), cleanup_old=True
        ),
    )
    monkeypatch.setattr(rotating_module.FileUtility, "exists", lambda _p: False)
    missing_dir._cleanup_old_files()
    missing_dir.close()

    backup_dir = tmp_path / "hybrid-bk"
    backup_dir.mkdir()
    for idx in range(3):
        (backup_dir / f"hy.log.{idx}").write_text("d", encoding="utf-8")
    config = RotationConfig(
        strategy=RotationStrategy.HYBRID,
        backup_dir=str(backup_dir),
        cleanup_old=True,
        max_time_files=1,
        max_size_files=2,
    )
    handler = _TestRotatingHandler(str(tmp_path / "hy.log"), config=config)
    monkeypatch.setattr(rotating_module.FileUtility, "exists", lambda _p: True)
    monkeypatch.setattr(rotating_module.FileUtility, "is_file", lambda _p: True)
    monkeypatch.setattr(
        rotating_module.FileUtility,
        "get_file_info",
        lambda p: SimpleNamespace(mtime=len(str(p))),
    )
    monkeypatch.setattr(
        rotating_module.FileUtility,
        "delete_file",
        lambda _p: (_ for _ in ()).throw(OSError("delete fail")),
    )
    with caplog.at_level("WARNING", logger="hydra_logger.handlers.rotating_handler"):
        handler._cleanup_old_files()
    assert "Failed to delete old rotated file" in caplog.text
    handler.close()


def test_rotating_flush_and_write_csv_and_error_paths(
    monkeypatch, caplog, tmp_path: Path
) -> None:
    path = tmp_path / "flush.log"
    handler = _TestRotatingHandler(str(path))
    handler._buffer.append("m")
    handler._string_buffer.append("m")
    handler._string_buffer_size = 1

    # Flush rotates when needed.
    monkeypatch.setattr(handler, "_should_rotate", lambda: True)
    rotated = {"count": 0}
    monkeypatch.setattr(
        handler,
        "_rotate_file",
        lambda: rotated.__setitem__("count", rotated["count"] + 1),
    )
    handler._flush_buffer()
    assert rotated["count"] == 1

    # Closed file path.
    class _Closed:
        closed = True

    handler._current_file = _Closed()
    handler._buffer.append("x")
    handler._string_buffer.append("x")
    handler._flush_buffer()

    # Generic flush failure path.
    class _BadWriter:
        closed = False

        def write(self, _m: str) -> None:
            raise RuntimeError("write fail")

        def flush(self) -> None:
            return None

    handler._current_file = _BadWriter()
    handler._buffer.append("x")
    handler._string_buffer.append("x")
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.rotating_handler"):
        handler._flush_buffer()
    assert "Rotating file buffer flush error" in caplog.text

    # CSV formatter header branch + write exception path.
    class CsvFormatter:
        def format_headers(self) -> str:
            return "h1,h2"

        def should_write_headers(self, _filename: str) -> bool:
            return True

        def mark_headers_written(self, _filename: str) -> None:
            return None

    class _TellWriter:
        def tell(self) -> int:
            return 0

        def write(self, _m: str) -> None:
            return None

        def flush(self) -> None:
            return None

        def close(self) -> None:
            return None

    handler.setFormatter(CsvFormatter())
    handler._current_file = _TellWriter()
    handler._write_to_file("entry\n")

    class _ExplodeWriter(_TellWriter):
        def write(self, _m: str) -> None:
            raise RuntimeError("boom")

    handler._current_file = _ExplodeWriter()
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.rotating_handler"):
        handler._write_to_file("entry\n")
    assert "Failed to write message to rotating file" in caplog.text
    handler.close()


def test_timed_size_hybrid_and_factory_uncovered_branches(
    monkeypatch, tmp_path: Path
) -> None:
    # Timed last-rotation fallback and backup naming paths.
    monkeypatch.setattr(rotating_module.FileUtility, "exists", lambda _p: False)
    timed = TimedRotatingFileHandler(
        filename=str(tmp_path / "timed-fallback.log"), when="day", interval=1
    )
    assert isinstance(timed._get_last_rotation_time(), datetime)
    assert timed._generate_backup_name().endswith(".log")
    timed_no_ext = TimedRotatingFileHandler(
        filename=str(tmp_path / "timed-noext.log"),
        when="day",
        interval=1,
    )
    # Toggle extension policy to hit non-extension backup-name branch.
    timed_no_ext._config.preserve_extension = False
    assert not timed_no_ext._generate_backup_name().endswith(".log")
    timed.close()
    timed_no_ext.close()

    # Size rotation "missing file" + sequence increment/no-extension branches.
    size = SizeRotatingFileHandler(
        filename=str(tmp_path / "size-fallback.log"), max_bytes=1
    )
    monkeypatch.setattr(rotating_module.FileUtility, "exists", lambda _p: False)
    assert size._should_rotate() is False
    size._config.preserve_extension = False
    size._config.backup_dir = str(tmp_path)
    # First candidate exists, force increment branch.
    first_candidate = tmp_path / "size-fallback.1"
    first_candidate.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        rotating_module.FileUtility, "exists", lambda p: str(p) == str(first_candidate)
    )
    generated = size._generate_backup_name()
    assert generated.endswith(".2")
    size.close()

    # Hybrid time branches and backup-name loop.
    hybrid = HybridRotatingFileHandler(
        filename=str(tmp_path / "hy-branches.log"), when="hour", interval=1
    )
    hybrid._last_rotation_time = datetime.now() - timedelta(hours=2)
    assert hybrid._should_rotate() is True
    hybrid._when = "midnight"
    hybrid._last_rotation_time = datetime.now() - timedelta(days=1)
    assert hybrid._should_rotate() is True
    hybrid._when = "none"
    assert hybrid._should_rotate() is False
    hybrid._config.backup_dir = str(tmp_path)
    existing = (
        tmp_path
        / f"hy-branches.{datetime.now().strftime(hybrid._config.time_format)}.1.log"
    )
    existing.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        rotating_module.FileUtility, "exists", lambda p: str(p) == str(existing)
    )
    assert ".2.log" in hybrid._generate_backup_name()
    hybrid.close()

    # Factory dispatch and hybrid time_unit pop path.
    assert isinstance(
        RotatingFileHandlerFactory.create_handler(
            "timed", filename=str(tmp_path / "fa-t.log")
        ),
        TimedRotatingFileHandler,
    )
    assert isinstance(
        RotatingFileHandlerFactory.create_handler(
            "size", filename=str(tmp_path / "fa-s.log")
        ),
        SizeRotatingFileHandler,
    )
    assert isinstance(
        RotatingFileHandlerFactory.create_handler(
            "hybrid", filename=str(tmp_path / "fa-h.log"), time_unit=TimeUnit.DAYS
        ),
        HybridRotatingFileHandler,
    )


def test_rotating_handler_remaining_emit_and_cleanup_branches(
    monkeypatch, caplog, tmp_path: Path
) -> None:
    handler = _TestRotatingHandler(str(tmp_path / "emit-branches.log"))

    class StreamingFmt:
        def format_for_streaming(self, _record):
            return "stream-only"

    class PlainFmt:
        def format(self, _record):
            return "plain"

    # format_for_streaming branch (no newline append)
    handler.setFormatter(StreamingFmt())
    handler.emit(LogRecord(level=20, level_name="INFO", message="x"))
    assert handler._string_buffer[-1] == "stream-only"

    # format branch + newline append for non-csv formatter
    handler.setFormatter(PlainFmt())
    handler.emit(LogRecord(level=20, level_name="INFO", message="x"))
    assert handler._string_buffer[-1].endswith("\n")

    # OSError/ValueError debug path in flush.
    class _OSErrorWriter:
        closed = False

        def write(self, _m: str) -> None:
            raise OSError("closed")

        def flush(self) -> None:
            return None

        def close(self) -> None:
            return None

    handler._current_file = _OSErrorWriter()
    handler._buffer.append("x")
    handler._string_buffer.append("x")
    with caplog.at_level("DEBUG", logger="hydra_logger.handlers.rotating_handler"):
        handler._flush_buffer()
    assert "Rotating file flush skipped due to closed or invalid handle" in caplog.text

    # Outer cleanup exception warning path.
    monkeypatch.setattr(
        rotating_module.os,
        "listdir",
        lambda _p: (_ for _ in ()).throw(RuntimeError("list fail")),
    )
    with caplog.at_level("WARNING", logger="hydra_logger.handlers.rotating_handler"):
        handler._cleanup_old_files()
    assert "Rotated file cleanup failed" in caplog.text
    handler.close()


def test_timed_and_hybrid_remaining_false_and_no_ext_name_branches(
    tmp_path: Path,
) -> None:
    timed = TimedRotatingFileHandler(
        filename=str(tmp_path / "timed-false.log"), when="none", interval=1
    )
    assert timed._should_rotate() is False
    timed.close()

    hybrid = HybridRotatingFileHandler(
        filename=str(tmp_path / "hy-noext.log"), when="none", interval=1
    )
    hybrid._config.preserve_extension = False
    name = hybrid._generate_backup_name()
    assert name.count(".") >= 2
    assert not name.endswith(".log")
    hybrid.close()
