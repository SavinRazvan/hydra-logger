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

from hydra_logger.utils.file_utility import (
    FileProcessor,
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
