"""
Role: Pytest coverage for file utility helpers.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates file operations, path helpers, and validation boundaries.
"""

from pathlib import Path

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
