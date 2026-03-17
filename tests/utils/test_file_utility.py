"""
Role: Pytest coverage for file utility helpers.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates file operations, path helpers, and validation boundaries.
"""

import builtins
import importlib
from pathlib import Path

import pytest

from hydra_logger.utils import file_utility as file_utility_module
from hydra_logger.utils.file_utility import (
    DirectoryScanner,
    FileProcessor,
    FilePermission,
    FileUtility,
    FileValidator,
    PathUtility,
)


def test_file_utility_copy_move_delete_and_listing(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("alpha", encoding="utf-8")
    copy_target = tmp_path / "copy.txt"
    moved_target = tmp_path / "moved.txt"

    assert FileUtility.copy_file(str(source), str(copy_target), overwrite=False)
    assert FileUtility.move_file(str(copy_target), str(moved_target), overwrite=False)
    assert FileUtility.exists(str(moved_target))
    assert FileUtility.delete_file(str(moved_target))
    listed = FileUtility.list_directory(str(tmp_path))
    assert "source.txt" in listed


def test_file_utility_size_permissions_and_timestamps(tmp_path: Path) -> None:
    file_path = tmp_path / "data.bin"
    file_path.write_bytes(b"1234")
    assert FileUtility.get_size(str(file_path)) == 4
    assert FileUtility.get_size_human(str(file_path)).endswith("B")
    permissions = FileUtility.get_permissions(str(file_path))
    assert len(permissions) == 3
    timestamps = FileUtility.get_timestamps(str(file_path))
    assert "modified" in timestamps


def test_path_utility_and_file_validator_helpers(tmp_path: Path) -> None:
    folder = tmp_path / "folder"
    folder.mkdir()
    file_path = folder / "event.log"
    file_path.write_text("entry", encoding="utf-8")

    changed = PathUtility.change_extension(str(file_path), "jsonl")
    ensured = PathUtility.ensure_extension(str(file_path), ".log")
    common = PathUtility.common_path(str(folder / "a"), str(folder / "b"))
    assert changed.endswith(".jsonl")
    assert ensured.endswith(".log")
    assert common

    assert FileValidator.validate_file_exists(str(file_path))
    assert FileValidator.validate_directory_exists(str(folder))
    assert FileValidator.validate_file_extension(str(file_path), [".log", ".txt"])
    assert FileValidator.validate_file_content(str(file_path), lambda content: "entry" in content)


def test_file_processor_text_json_and_append(tmp_path: Path) -> None:
    text_path = tmp_path / "notes.txt"
    json_path = tmp_path / "meta.json"

    assert FileProcessor.write_text_file(str(text_path), "line1")
    assert FileProcessor.append_text(str(text_path), "\nline2")
    text = FileProcessor.read_text_file(str(text_path))
    assert "line2" in text

    assert FileProcessor.write_json_file(str(json_path), {"k": "v"})
    payload = FileProcessor.read_json_file(str(json_path))
    assert payload["k"] == "v"


def test_file_utility_info_and_finders_and_delete_directory(tmp_path: Path) -> None:
    root = tmp_path / "scan"
    nested = root / "nested"
    nested.mkdir(parents=True)
    text_file = nested / "a.txt"
    py_file = root / "b.py"
    text_file.write_text("line1\nline2\n", encoding="utf-8")
    py_file.write_text("print('x')\n", encoding="utf-8")

    info = FileUtility.get_file_info(str(text_file), include_content=True)
    assert info.line_count == 2
    assert info.md5_hash
    assert info.to_dict()["name"] == "a.txt"

    matches_recursive = FileUtility.find_files("*.txt", root_path=str(root), recursive=True)
    matches_non_recursive = FileUtility.find_files(
        "*.py", root_path=str(root), recursive=False
    )
    assert any(path.endswith("a.txt") for path in matches_recursive)
    assert any(path.endswith("b.py") for path in matches_non_recursive)

    removable = tmp_path / "remove_me"
    removable.mkdir()
    assert FileUtility.delete_directory(str(removable), recursive=False) is True


def test_path_utility_and_validator_extended_branches(tmp_path: Path) -> None:
    folder = tmp_path / "p"
    folder.mkdir()
    file_path = folder / "exec.sh"
    file_path.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    file_path.chmod(0o755)

    normalized = PathUtility.normalize_path(str(folder / ".." / "p" / "exec.sh"))
    absolute = PathUtility.absolute_path(str(file_path))
    relative = PathUtility.relative_path(absolute, start=str(tmp_path))
    joined = PathUtility.join_paths(str(tmp_path), "p", "exec.sh")
    split_dir, split_name = PathUtility.split_path(str(file_path))
    split_base, split_ext = PathUtility.split_extension(str(file_path))
    expanded = PathUtility.expand_path("$HOME")
    resolved = PathUtility.resolve_path(str(file_path))
    assert normalized.endswith("exec.sh")
    assert PathUtility.is_absolute(absolute) is True
    assert PathUtility.is_relative(relative) is True
    assert joined.endswith("exec.sh")
    assert split_name == "exec.sh"
    assert split_ext == ".sh"
    assert split_base.endswith("exec")
    assert expanded
    assert resolved.endswith("exec.sh")
    assert PathUtility.get_directory(str(file_path)).endswith("p")
    assert PathUtility.get_filename(str(file_path)) == "exec.sh"
    assert PathUtility.get_extension(str(file_path)) == ".sh"

    assert FileValidator.validate_path_exists(str(file_path))
    assert FileValidator.validate_file_readable(str(file_path))
    assert FileValidator.validate_file_writable(str(file_path))
    assert FileValidator.validate_file_executable(str(file_path))
    assert FileValidator.validate_file_permissions(str(file_path), FilePermission.ALL)
    assert FileValidator.validate_file_size(str(file_path), min_size=1, max_size=10000)


def test_file_processor_binary_lines_temp_and_optional_formats(
    monkeypatch, tmp_path: Path
) -> None:
    binary_path = tmp_path / "data.bin"
    lines_path = tmp_path / "lines.txt"
    assert FileProcessor.write_binary_file(str(binary_path), b"\x00\x01")
    assert FileProcessor.read_binary_file(str(binary_path)) == b"\x00\x01"

    assert FileProcessor.write_lines(str(lines_path), ["a\n", "b\n"])
    assert FileProcessor.read_lines(str(lines_path)) == ["a\n", "b\n"]

    temp_file = FileProcessor.create_temp_file(suffix=".tmp", prefix="x_", delete=False)
    temp_dir = FileProcessor.create_temp_directory(prefix="y_")
    assert Path(temp_file).name.startswith("x_")
    assert Path(temp_dir).name.startswith("y_")

    monkeypatch.setattr(file_utility_module, "YAML_AVAILABLE", False)
    monkeypatch.setattr(file_utility_module, "yaml", None)
    try:
        FileProcessor.read_yaml_file(str(lines_path))
    except ImportError as exc:
        assert "PyYAML" in str(exc)
    else:
        raise AssertionError("Expected ImportError when YAML support is unavailable")

    monkeypatch.setattr(file_utility_module, "TOML_AVAILABLE", False)
    monkeypatch.setattr(file_utility_module, "toml", None)
    try:
        FileProcessor.read_toml_file(str(lines_path))
    except ImportError as exc:
        assert "toml is required" in str(exc)
    else:
        raise AssertionError("Expected ImportError when TOML support is unavailable")


def test_directory_scanner_tree_and_stats(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    sub = root / "sub"
    hidden = root / ".hidden"
    sub.mkdir(parents=True)
    hidden.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    (sub / "b.py").write_text("print('b')", encoding="utf-8")
    (hidden / "c.log").write_text("c", encoding="utf-8")

    files_default = DirectoryScanner.scan_directory(str(root), recursive=True)
    files_with_hidden = DirectoryScanner.scan_directory(
        str(root), recursive=True, include_hidden=True
    )
    by_pattern = DirectoryScanner.scan_by_pattern(str(root), "*.py", recursive=True)
    by_ext = DirectoryScanner.scan_by_extension(str(root), [".txt", "py"], recursive=True)
    tree = DirectoryScanner.get_directory_tree(str(root), max_depth=2)
    stats = DirectoryScanner.get_directory_stats(str(root))

    assert all("/.hidden/" not in path for path in files_default)
    assert any("/.hidden/" in path for path in files_with_hidden)
    assert any(path.endswith("b.py") for path in by_pattern)
    assert any(path.endswith("a.txt") for path in by_ext)
    assert "sub" in tree
    assert stats["total_files"] >= 2


def test_file_utility_error_and_type_detection_branches(monkeypatch, tmp_path: Path) -> None:
    regular_file = tmp_path / "regular.txt"
    regular_file.write_text("hello", encoding="utf-8")
    folder = tmp_path / "d"
    folder.mkdir()
    symlink = tmp_path / "regular.link"
    symlink.symlink_to(regular_file)

    assert FileUtility.is_file(str(regular_file))
    assert FileUtility.is_directory(str(folder))
    assert FileUtility.is_symlink(str(symlink))
    assert FileUtility.is_hidden(str(tmp_path / ".hidden"))

    with pytest.raises(FileNotFoundError):
        FileUtility.get_size(str(tmp_path / "missing.txt"))
    with pytest.raises(FileNotFoundError):
        FileUtility.get_timestamps(str(tmp_path / "missing"))
    with pytest.raises(FileNotFoundError):
        FileUtility.get_permissions(str(tmp_path / "missing"))
    with pytest.raises(NotADirectoryError):
        FileUtility.list_directory(str(regular_file))

    assert FileUtility._format_size(0) == "0 B"
    assert FileUtility._format_size(1536).endswith("KB")

    category_files = {
        "sample.docx": file_utility_module.FileType.DOCUMENT,
        "sample.png": file_utility_module.FileType.IMAGE,
        "sample.mp3": file_utility_module.FileType.AUDIO,
        "sample.mp4": file_utility_module.FileType.VIDEO,
        "sample.zip": file_utility_module.FileType.ARCHIVE,
        "sample.json": file_utility_module.FileType.DATA,
    }
    for name, expected in category_files.items():
        path = tmp_path / name
        path.write_text("x", encoding="utf-8")
        assert FileUtility._detect_file_type(str(path)) == expected

    assert FileUtility._detect_file_type(str(folder)) == file_utility_module.FileType.UNKNOWN

    bom_file = tmp_path / "bom.unknown"
    bom_file.write_bytes(b"\xef\xbb\xbfhello")
    assert FileUtility._detect_file_type(str(bom_file)) == file_utility_module.FileType.TEXT

    binary_file = tmp_path / "binary.unknown"
    binary_file.write_bytes(b"\xff\xfe\x00\x01")
    assert FileUtility._detect_file_type(str(binary_file)) == file_utility_module.FileType.UNKNOWN

    utf8_file = tmp_path / "utf8.unknown"
    utf8_file.write_bytes(b"plain utf8 text")
    assert FileUtility._detect_file_type(str(utf8_file)) == file_utility_module.FileType.TEXT

    original_open = builtins.open

    def failing_open(path, mode="r", *args, **kwargs):
        if path == str(binary_file) and "rb" in mode:
            raise OSError("open failed")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", failing_open)
    assert FileUtility._detect_file_type(str(binary_file)) == file_utility_module.FileType.UNKNOWN


def test_file_utility_failure_paths_for_operations(monkeypatch, tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    src.write_text("x", encoding="utf-8")
    dst = tmp_path / "dst.txt"
    dst.write_text("y", encoding="utf-8")

    assert FileUtility.copy_file(str(src), str(dst), overwrite=False) is False
    assert FileUtility.move_file(str(src), str(dst), overwrite=False) is False
    assert FileUtility.delete_file(str(tmp_path / "missing.txt")) is False

    monkeypatch.setattr(file_utility_module.os, "remove", lambda _: (_ for _ in ()).throw(OSError("remove")))
    assert FileUtility.delete_file(str(dst)) is False

    monkeypatch.setattr(
        file_utility_module.os,
        "makedirs",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("mkdir")),
    )
    assert FileUtility.create_directory(str(tmp_path / "new_dir")) is False
    assert FileUtility.ensure_directory_exists(str(tmp_path / "new_dir_2")) is False

    monkeypatch.setattr(
        file_utility_module.os,
        "access",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("access")),
    )
    assert FileUtility.is_writable(str(tmp_path / "file.txt")) is False
    assert FileUtility.is_readable(str(src)) is False

    non_empty = tmp_path / "non_empty"
    non_empty.mkdir()
    (non_empty / "x.txt").write_text("x", encoding="utf-8")
    assert FileUtility.delete_directory(str(non_empty), recursive=False) is False

    removable = tmp_path / "remove_recursive"
    removable.mkdir()
    (removable / "n.txt").write_text("n", encoding="utf-8")
    assert FileUtility.delete_directory(str(removable), recursive=True) is True


def test_get_file_info_handles_content_failures(monkeypatch, tmp_path: Path) -> None:
    text_file = tmp_path / "content.txt"
    text_file.write_text("a\nb\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        FileUtility.get_file_info(str(tmp_path / "missing.txt"), include_content=True)

    original_open = builtins.open

    def line_count_open(path, mode="r", *args, **kwargs):
        if path == str(text_file) and mode == "r":
            raise OSError("read failed")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", line_count_open)
    monkeypatch.setattr(
        file_utility_module.FileUtility,
        "_calculate_hash",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("hash failed")),
    )

    info = file_utility_module.FileUtility.get_file_info(str(text_file), include_content=True)
    assert info.line_count is None
    assert info.md5_hash is None
    assert info.sha1_hash is None
    assert info.sha256_hash is None


def test_file_validator_edge_and_failure_branches(tmp_path: Path) -> None:
    path = tmp_path / "exec.sh"
    path.write_text("#!/bin/sh\necho x\n", encoding="utf-8")
    path.chmod(0o755)

    assert FileValidator.validate_file_permissions(
        str(path), file_utility_module.FilePermission.READ
    )
    assert FileValidator.validate_file_permissions(
        str(path), file_utility_module.FilePermission.WRITE
    )
    assert FileValidator.validate_file_permissions(
        str(path), file_utility_module.FilePermission.EXECUTE
    )
    assert FileValidator.validate_file_permissions(str(path), "bad_permission") is False

    assert FileValidator.validate_file_size(str(tmp_path / "missing.bin")) is False
    assert FileValidator.validate_file_size(str(path), min_size=10_000) is False
    assert FileValidator.validate_file_size(str(path), max_size=1) is False

    assert FileValidator.validate_file_content(str(tmp_path / "missing.txt"), lambda _c: True) is False


def test_file_processor_failure_paths_and_optional_format_success(monkeypatch, tmp_path: Path) -> None:
    text_path = tmp_path / "text.txt"
    text_path.write_text("ok", encoding="utf-8")

    class DummyYaml:
        @staticmethod
        def safe_load(stream):
            return {"loaded": stream.read().strip()}

        @staticmethod
        def dump(_data, _stream, **_kwargs):
            raise OSError("yaml dump failed")

    class DummyToml:
        @staticmethod
        def load(_stream):
            return {"ok": True}

        @staticmethod
        def dump(_data, _stream):
            raise OSError("toml dump failed")

    monkeypatch.setattr(file_utility_module, "YAML_AVAILABLE", True)
    monkeypatch.setattr(file_utility_module, "yaml", DummyYaml)
    assert FileProcessor.read_yaml_file(str(text_path)) == {"loaded": "ok"}
    assert FileProcessor.write_yaml_file(str(tmp_path / "out.yaml"), {"k": "v"}) is False

    monkeypatch.setattr(file_utility_module, "TOML_AVAILABLE", True)
    monkeypatch.setattr(file_utility_module, "toml", DummyToml)
    assert FileProcessor.read_toml_file(str(text_path)) == {"ok": True}
    assert FileProcessor.write_toml_file(str(tmp_path / "out.toml"), {"k": "v"}) is False

    monkeypatch.setattr(
        builtins,
        "open",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("open failed")),
    )
    assert FileProcessor.write_text_file(str(tmp_path / "a.txt"), "x") is False
    assert FileProcessor.write_binary_file(str(tmp_path / "a.bin"), b"x") is False
    assert FileProcessor.write_lines(str(tmp_path / "a.lines"), ["x\n"]) is False
    assert FileProcessor.append_text(str(tmp_path / "a.txt"), "x") is False
    assert FileProcessor.write_json_file(str(tmp_path / "a.json"), {"x": 1}) is False


def test_file_processor_write_success_and_importerror_paths(monkeypatch, tmp_path: Path) -> None:
    out_yaml = tmp_path / "good.yaml"
    out_toml = tmp_path / "good.toml"

    class GoodYaml:
        @staticmethod
        def dump(data, stream, **_kwargs):
            stream.write(str(data))

    class GoodToml:
        @staticmethod
        def dump(data, stream):
            stream.write(str(data))

    monkeypatch.setattr(file_utility_module, "YAML_AVAILABLE", True)
    monkeypatch.setattr(file_utility_module, "yaml", GoodYaml)
    assert FileProcessor.write_yaml_file(str(out_yaml), {"a": 1}) is True

    monkeypatch.setattr(file_utility_module, "TOML_AVAILABLE", True)
    monkeypatch.setattr(file_utility_module, "toml", GoodToml)
    assert FileProcessor.write_toml_file(str(out_toml), {"a": 1}) is True

    monkeypatch.setattr(file_utility_module, "YAML_AVAILABLE", False)
    monkeypatch.setattr(file_utility_module, "yaml", None)
    with pytest.raises(ImportError):
        FileProcessor.write_yaml_file(str(out_yaml), {"a": 1})

    monkeypatch.setattr(file_utility_module, "TOML_AVAILABLE", False)
    monkeypatch.setattr(file_utility_module, "toml", None)
    with pytest.raises(ImportError):
        FileProcessor.write_toml_file(str(out_toml), {"a": 1})


def test_directory_scanner_non_recursive_and_tree_error_branches(
    monkeypatch, tmp_path: Path
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    (root / "b.py").write_text("print('b')", encoding="utf-8")
    sub = root / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("nested", encoding="utf-8")
    hidden = root / ".c.txt"
    hidden.write_text("c", encoding="utf-8")

    non_recursive = DirectoryScanner.scan_directory(str(root), recursive=False)
    pattern_non_recursive = DirectoryScanner.scan_by_pattern(
        str(root), "*.py", recursive=False
    )
    extension_non_recursive = DirectoryScanner.scan_by_extension(
        str(root), [".txt"], recursive=False
    )
    shallow_tree = DirectoryScanner.get_directory_tree(str(root), max_depth=0)

    assert any(path.endswith("a.txt") for path in non_recursive)
    assert any(path.endswith("b.py") for path in pattern_non_recursive)
    assert any(path.endswith(".c.txt") for path in extension_non_recursive)
    assert shallow_tree["a.txt"]["type"] == "file"

    monkeypatch.setattr(file_utility_module.os, "listdir", lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError))
    assert "<permission_denied>" in DirectoryScanner.get_directory_tree(str(root))

    monkeypatch.setattr(file_utility_module.os, "listdir", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    assert "<error>" in DirectoryScanner.get_directory_tree(str(root))


def test_directory_stats_handles_file_stat_failures(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "stats"
    root.mkdir()
    (root / "x.txt").write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        file_utility_module.os.path,
        "getsize",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("size failed")),
    )
    stats = DirectoryScanner.get_directory_stats(str(root))
    assert stats["total_files"] == 1
    assert stats["total_size"] == 0


def test_misc_success_branches_for_directory_and_access_helpers(tmp_path: Path) -> None:
    created = tmp_path / "created"
    ensured = tmp_path / "ensured"
    existing_file = tmp_path / "existing.txt"
    existing_file.write_text("x", encoding="utf-8")

    assert FileUtility.create_directory(str(created)) is True
    assert FileUtility.ensure_directory_exists(str(ensured)) is True
    assert FileUtility.is_writable(str(existing_file)) is True
    assert FileUtility.is_readable(str(tmp_path / "missing.txt")) is False
    assert PathUtility.ensure_extension("name.txt", ".txt") == "name.txt"
    assert PathUtility.ensure_extension("name.txt", "txt") == "name.txt"
    assert PathUtility.ensure_extension("name", ".txt") == "name.txt"


def test_file_utility_optional_dependency_import_fallbacks(monkeypatch) -> None:
    original_import = builtins.__import__

    def _mock_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name in {"yaml", "toml"}:
            raise ImportError(f"missing optional dependency: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _mock_import)
    reloaded = importlib.reload(file_utility_module)
    assert reloaded.YAML_AVAILABLE is False
    assert reloaded.TOML_AVAILABLE is False
    assert reloaded.yaml is None
    assert reloaded.toml is None

    monkeypatch.setattr(builtins, "__import__", original_import)
    importlib.reload(file_utility_module)
