"""
File System Utilities for Hydra-Logger

This module provides comprehensive file and directory utility functions including
file operations, path management, validation, processing, and directory scanning.
It supports various file types, permissions, and metadata extraction.

FEATURES:
- FileUtils: General file operations and information
- PathManager: Path manipulation and normalization
- FileValidator: File and directory validation
- FileProcessor: File reading, writing, and processing
- DirectoryScanner: Directory scanning and tree structure
- File type detection and metadata extraction
- Permission checking and validation
- Checksum calculation and integrity verification

FILE OPERATIONS:
- File existence and type checking
- File copying, moving, and deletion
- Directory creation and management
- Permission and access validation
- File size and timestamp operations

PATH MANAGEMENT:
- Path normalization and resolution
- Relative and absolute path conversion
- Path joining and splitting
- Extension manipulation
- Symbolic link resolution

USAGE:
    from hydra_logger.utils import FileUtils, PathManager, FileValidator
    
    # File operations
    exists = FileUtils.exists("/path/to/file")
    size = FileUtils.get_size("/path/to/file")
    info = FileUtils.get_file_info("/path/to/file")
    
    # Path management
    normalized = PathManager.normalize_path("../relative/path")
    absolute = PathManager.absolute_path("file.txt")
    joined = PathManager.join_paths("dir", "subdir", "file.txt")
    
    # File validation
    is_valid = FileValidator.validate_file_exists("/path/to/file")
    is_readable = FileValidator.validate_file_readable("/path/to/file")
    
    # File processing
    from hydra_logger.utils import FileProcessor
    content = FileProcessor.read_text_file("/path/to/file")
    success = FileProcessor.write_text_file("/path/to/file", "content")
"""

import os
import shutil
import hashlib
import mimetypes
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import tempfile
import json
import yaml
import toml
class FileType(Enum):
    """File type categories."""

    TEXT = "text"
    BINARY = "binary"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    DOCUMENT = "document"
    CODE = "code"
    DATA = "data"
    UNKNOWN = "unknown"


class FilePermission(Enum):
    """File permission levels."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ALL = "all"


@dataclass
class FileInfo:
    """File information and metadata."""

    # Basic information
    path: str
    name: str
    size: int
    file_type: FileType

    # Timestamps
    created: float
    modified: float
    accessed: float

    # File attributes
    is_file: bool
    is_directory: bool
    is_symlink: bool
    is_hidden: bool

    # Permissions
    permissions: str
    owner: Optional[str] = None
    group: Optional[str] = None

    # Content information
    mime_type: Optional[str] = None
    encoding: Optional[str] = None
    line_count: Optional[int] = None

    # Checksums
    md5_hash: Optional[str] = None
    sha1_hash: Optional[str] = None
    sha256_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert file info to dictionary."""
        return {
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "file_type": self.file_type.value,
            "created": self.created,
            "modified": self.modified,
            "accessed": self.accessed,
            "is_file": self.is_file,
            "is_directory": self.is_directory,
            "is_symlink": self.is_symlink,
            "is_hidden": self.is_hidden,
            "permissions": self.permissions,
            "owner": self.owner,
            "group": self.group,
            "mime_type": self.mime_type,
            "encoding": self.encoding,
            "line_count": self.line_count,
            "md5_hash": self.md5_hash,
            "sha1_hash": self.sha1_hash,
            "sha256_hash": self.sha256_hash,
        }


class FileUtils:
    """General file utility functions."""

    @staticmethod
    def exists(path: str) -> bool:
        """Check if file or directory exists."""
        return os.path.exists(path)

    @staticmethod
    def is_file(path: str) -> bool:
        """Check if path is a file."""
        return os.path.isfile(path)

    @staticmethod
    def is_directory(path: str) -> bool:
        """Check if path is a directory."""
        return os.path.isdir(path)

    @staticmethod
    def is_symlink(path: str) -> bool:
        """Check if path is a symbolic link."""
        return os.path.islink(path)

    @staticmethod
    def is_hidden(path: str) -> bool:
        """Check if file or directory is hidden."""
        name = os.path.basename(path)
        return name.startswith(".")

    @staticmethod
    def get_size(path: str) -> int:
        """Get file size in bytes."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File not found: {path}")
        return os.path.getsize(path)

    @staticmethod
    def get_size_human(path: str) -> str:
        """Get file size in human-readable format."""
        size = FileUtils.get_size(path)
        return FileUtils._format_size(size)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format size in bytes to human-readable format."""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    @staticmethod
    def get_timestamps(path: str) -> Dict[str, float]:
        """Get file timestamps."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")

        stat = os.stat(path)
        return {
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
        }

    @staticmethod
    def get_permissions(path: str) -> str:
        """Get file permissions as string."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")

        stat = os.stat(path)
        return oct(stat.st_mode)[-3:]

    @staticmethod
    def copy_file(source: str, destination: str, overwrite: bool = False) -> bool:
        """Copy a file from source to destination."""
        try:
            if os.path.exists(destination) and not overwrite:
                raise FileExistsError(f"Destination file exists: {destination}")

            shutil.copy2(source, destination)
            return True
        except Exception:
            return False

    @staticmethod
    def move_file(source: str, destination: str, overwrite: bool = False) -> bool:
        """Move a file from source to destination."""
        try:
            if os.path.exists(destination) and not overwrite:
                raise FileExistsError(f"Destination file exists: {destination}")

            shutil.move(source, destination)
            return True
        except Exception:
            return False

    @staticmethod
    def delete_file(path: str) -> bool:
        """Delete a file."""
        try:
            if os.path.isfile(path):
                os.remove(path)
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def create_directory(path: str, parents: bool = True) -> bool:
        """Create a directory."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False

    @staticmethod
    def ensure_directory_exists(path: str, parents: bool = True) -> bool:
        """Ensure a directory exists, create it if it doesn't."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False

    @staticmethod
    def is_writable(path: str) -> bool:
        """Check if a file or directory is writable."""
        try:
            if os.path.exists(path):
                return os.access(path, os.W_OK)
            else:
                # Check if parent directory is writable
                parent_dir = os.path.dirname(path)
                return os.access(parent_dir, os.W_OK)
        except Exception:
            return False

    @staticmethod
    def is_readable(path: str) -> bool:
        """Check if a file or directory is readable."""
        try:
            if os.path.exists(path):
                return os.access(path, os.R_OK)
            else:
                return False
        except Exception:
            return False

    @staticmethod
    def delete_directory(path: str, recursive: bool = False) -> bool:
        """Delete a directory."""
        try:
            if recursive:
                shutil.rmtree(path)
            else:
                os.rmdir(path)
            return True
        except Exception:
            return False

    @staticmethod
    def list_directory(path: str, include_hidden: bool = False) -> List[str]:
        """List contents of a directory."""
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Not a directory: {path}")

        items = os.listdir(path)
        if not include_hidden:
            items = [item for item in items if not item.startswith(".")]

        return sorted(items)

    @staticmethod
    def find_files(
        pattern: str, root_path: str = ".", recursive: bool = True
    ) -> List[str]:
        """Find files matching a pattern."""
        import glob
        import fnmatch

        matches = []

        if recursive:
            for root, dirs, files in os.walk(root_path):
                for file in files:
                    if fnmatch.fnmatch(file, pattern):
                        matches.append(os.path.join(root, file))
        else:
            matches = glob.glob(os.path.join(root_path, pattern))

        return matches

    @staticmethod
    def get_file_info(path: str, include_content: bool = False) -> FileInfo:
        """Get comprehensive file information."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")

        stat = os.stat(path)

        # Basic information
        file_type = FileUtils._detect_file_type(path)
        name = os.path.basename(path)

        # Timestamps
        created = stat.st_ctime
        modified = stat.st_mtime
        accessed = stat.st_atime

        # File attributes
        is_file = os.path.isfile(path)
        is_directory = os.path.isdir(path)
        is_symlink = os.path.islink(path)
        is_hidden = FileUtils.is_hidden(path)

        # Permissions
        permissions = FileUtils.get_permissions(path)

        # Content information
        mime_type = None
        encoding = None
        line_count = None

        if is_file:
            mime_type, encoding = mimetypes.guess_type(path)
            if include_content and file_type == FileType.TEXT:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        line_count = sum(1 for _ in f)
                except Exception:
                    pass

        # Checksums
        md5_hash = None
        sha1_hash = None
        sha256_hash = None

        if include_content and is_file:
            try:
                md5_hash = FileUtils._calculate_hash(path, "md5")
                sha1_hash = FileUtils._calculate_hash(path, "sha1")
                sha256_hash = FileUtils._calculate_hash(path, "sha256")
            except Exception:
                pass

        return FileInfo(
            path=path,
            name=name,
            size=stat.st_size,
            file_type=file_type,
            created=created,
            modified=modified,
            accessed=accessed,
            is_file=is_file,
            is_directory=is_directory,
            is_symlink=is_symlink,
            is_hidden=is_hidden,
            permissions=permissions,
            mime_type=mime_type,
            encoding=encoding,
            line_count=line_count,
            md5_hash=md5_hash,
            sha1_hash=sha1_hash,
            sha256_hash=sha256_hash,
        )

    @staticmethod
    def _detect_file_type(path: str) -> FileType:
        """Detect file type based on extension and content."""
        if os.path.isdir(path):
            return FileType.UNKNOWN

        ext = os.path.splitext(path)[1].lower()

        # Text files
        text_extensions = {".txt", ".md", ".rst", ".log", ".ini", ".cfg", ".conf"}
        if ext in text_extensions:
            return FileType.TEXT

        # Code files
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
        }
        if ext in code_extensions:
            return FileType.CODE

        # Document files
        doc_extensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".odt",
            ".ods",
            ".odp",
        }
        if ext in doc_extensions:
            return FileType.DOCUMENT

        # Image files
        image_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".svg",
            ".webp",
        }
        if ext in image_extensions:
            return FileType.IMAGE

        # Audio files
        audio_extensions = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"}
        if ext in audio_extensions:
            return FileType.AUDIO

        # Video files
        video_extensions = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"}
        if ext in video_extensions:
            return FileType.VIDEO

        # Archive files
        archive_extensions = {".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"}
        if ext in archive_extensions:
            return FileType.ARCHIVE

        # Data files
        data_extensions = {
            ".json",
            ".xml",
            ".csv",
            ".yaml",
            ".yml",
            ".toml",
            ".sql",
            ".db",
        }
        if ext in data_extensions:
            return FileType.DATA

        # Try to detect text files by content
        try:
            with open(path, "rb") as f:
                chunk = f.read(1024)
                if chunk.startswith(b"\xef\xbb\xbf"):  # UTF-8 BOM
                    return FileType.TEXT
                try:
                    chunk.decode("utf-8")
                    return FileType.TEXT
                except UnicodeDecodeError:
                    pass
        except Exception:
            pass

        return FileType.UNKNOWN

    @staticmethod
    def _calculate_hash(path: str, algorithm: str) -> str:
        """Calculate file hash using specified algorithm."""
        hash_func = getattr(hashlib, algorithm)
        hash_obj = hash_func()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()


class PathManager:
    """Path management utilities."""

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize a file path."""
        return os.path.normpath(path)

    @staticmethod
    def absolute_path(path: str) -> str:
        """Convert relative path to absolute path."""
        return os.path.abspath(path)

    @staticmethod
    def relative_path(path: str, start: str = ".") -> str:
        """Convert absolute path to relative path."""
        return os.path.relpath(path, start)

    @staticmethod
    def join_paths(*paths: str) -> str:
        """Join path components."""
        return os.path.join(*paths)

    @staticmethod
    def split_path(path: str) -> Tuple[str, str]:
        """Split path into directory and filename."""
        return os.path.split(path)

    @staticmethod
    def split_extension(path: str) -> Tuple[str, str]:
        """Split path into filename and extension."""
        return os.path.splitext(path)

    @staticmethod
    def get_directory(path: str) -> str:
        """Get directory part of path."""
        return os.path.dirname(path)

    @staticmethod
    def get_filename(path: str) -> str:
        """Get filename part of path."""
        return os.path.basename(path)

    @staticmethod
    def get_extension(path: str) -> str:
        """Get file extension."""
        return os.path.splitext(path)[1]

    @staticmethod
    def change_extension(path: str, new_extension: str) -> str:
        """Change file extension."""
        base, _ = os.path.splitext(path)
        if not new_extension.startswith("."):
            new_extension = "." + new_extension
        return base + new_extension

    @staticmethod
    def ensure_extension(path: str, extension: str) -> str:
        """Ensure path has specified extension."""
        if not extension.startswith("."):
            extension = "." + extension

        if path.endswith(extension):
            return path

        return path + extension

    @staticmethod
    def is_absolute(path: str) -> bool:
        """Check if path is absolute."""
        return os.path.isabs(path)

    @staticmethod
    def is_relative(path: str) -> bool:
        """Check if path is relative."""
        return not os.path.isabs(path)

    @staticmethod
    def resolve_path(path: str) -> str:
        """Resolve symbolic links and return canonical path."""
        return os.path.realpath(path)

    @staticmethod
    def expand_path(path: str) -> str:
        """Expand user and environment variables in path."""
        return os.path.expanduser(os.path.expandvars(path))

    @staticmethod
    def common_path(path1: str, path2: str) -> str:
        """Find common path prefix between two paths."""
        path1_parts = Path(path1).parts
        path2_parts = Path(path2).parts

        common = []
        for part1, part2 in zip(path1_parts, path2_parts):
            if part1 == part2:
                common.append(part1)
            else:
                break

        return os.path.join(*common) if common else ""


class FileValidator:
    """File validation utilities."""

    @staticmethod
    def validate_file_exists(path: str) -> bool:
        """Validate that file exists."""
        return os.path.isfile(path)

    @staticmethod
    def validate_directory_exists(path: str) -> bool:
        """Validate that directory exists."""
        return os.path.isdir(path)

    @staticmethod
    def validate_path_exists(path: str) -> bool:
        """Validate that path exists."""
        return os.path.exists(path)

    @staticmethod
    def validate_file_readable(path: str) -> bool:
        """Validate that file is readable."""
        return os.access(path, os.R_OK)

    @staticmethod
    def validate_file_writable(path: str) -> bool:
        """Validate that file is writable."""
        return os.access(path, os.W_OK)

    @staticmethod
    def validate_file_executable(path: str) -> bool:
        """Validate that file is executable."""
        return os.access(path, os.X_OK)

    @staticmethod
    def validate_file_permissions(path: str, permissions: FilePermission) -> bool:
        """Validate file permissions."""
        if permissions == FilePermission.READ:
            return FileValidator.validate_file_readable(path)
        elif permissions == FilePermission.WRITE:
            return FileValidator.validate_file_writable(path)
        elif permissions == FilePermission.EXECUTE:
            return FileValidator.validate_file_executable(path)
        elif permissions == FilePermission.ALL:
            return (
                FileValidator.validate_file_readable(path)
                and FileValidator.validate_file_writable(path)
                and FileValidator.validate_file_executable(path)
            )
        else:
            return False

    @staticmethod
    def validate_file_size(
        path: str, min_size: Optional[int] = None, max_size: Optional[int] = None
    ) -> bool:
        """Validate file size constraints."""
        if not os.path.isfile(path):
            return False

        size = os.path.getsize(path)

        if min_size is not None and size < min_size:
            return False

        if max_size is not None and size > max_size:
            return False

        return True

    @staticmethod
    def validate_file_extension(path: str, allowed_extensions: List[str]) -> bool:
        """Validate file extension."""
        ext = os.path.splitext(path)[1].lower()
        return ext in [ext.lower() for ext in allowed_extensions]

    @staticmethod
    def validate_file_content(path: str, validator_func: Callable[[str], bool]) -> bool:
        """Validate file content using custom validator function."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return validator_func(content)
        except Exception:
            return False


class FileProcessor:
    """File processing utilities."""

    @staticmethod
    def read_text_file(path: str, encoding: str = "utf-8") -> str:
        """Read text file content."""
        with open(path, "r", encoding=encoding) as f:
            return f.read()

    @staticmethod
    def write_text_file(path: str, content: str, encoding: str = "utf-8") -> bool:
        """Write text content to file."""
        try:
            with open(path, "w", encoding=encoding) as f:
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def read_binary_file(path: str) -> bytes:
        """Read binary file content."""
        with open(path, "rb") as f:
            return f.read()

    @staticmethod
    def write_binary_file(path: str, content: bytes) -> bool:
        """Write binary content to file."""
        try:
            with open(path, "wb") as f:
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def read_lines(path: str, encoding: str = "utf-8") -> List[str]:
        """Read file lines."""
        with open(path, "r", encoding=encoding) as f:
            return f.readlines()

    @staticmethod
    def write_lines(path: str, lines: List[str], encoding: str = "utf-8") -> bool:
        """Write lines to file."""
        try:
            with open(path, "w", encoding=encoding) as f:
                f.writelines(lines)
            return True
        except Exception:
            return False

    @staticmethod
    def append_text(path: str, content: str, encoding: str = "utf-8") -> bool:
        """Append text to file."""
        try:
            with open(path, "a", encoding=encoding) as f:
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def read_json_file(path: str) -> Any:
        """Read JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def write_json_file(path: str, data: Any, indent: int = 2) -> bool:
        """Write JSON file."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception:
            return False

    @staticmethod
    def read_yaml_file(path: str) -> Any:
        """Read YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def write_yaml_file(path: str, data: Any) -> bool:
        """Write YAML file."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception:
            return False

    @staticmethod
    def read_toml_file(path: str) -> Any:
        """Read TOML file."""
        with open(path, "r", encoding="utf-8") as f:
            return toml.load(f)

    @staticmethod
    def write_toml_file(path: str, data: Any) -> bool:
        """Write TOML file."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                toml.dump(data, f)
            return True
        except Exception:
            return False

    @staticmethod
    def create_temp_file(
        suffix: str = "", prefix: str = "temp_", delete: bool = True
    ) -> str:
        """Create a temporary file."""
        temp_file = tempfile.NamedTemporaryFile(
            suffix=suffix, prefix=prefix, delete=delete
        )
        return temp_file.name

    @staticmethod
    def create_temp_directory(prefix: str = "temp_") -> str:
        """Create a temporary directory."""
        return tempfile.mkdtemp(prefix=prefix)


class DirectoryScanner:
    """Directory scanning utilities."""

    @staticmethod
    def scan_directory(
        path: str, recursive: bool = True, include_hidden: bool = False
    ) -> List[str]:
        """Scan directory and return all files."""
        files = []

        if recursive:
            for root, dirs, filenames in os.walk(path):
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith(".")]

                for filename in filenames:
                    if include_hidden or not filename.startswith("."):
                        files.append(os.path.join(root, filename))
        else:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    if include_hidden or not item.startswith("."):
                        files.append(item_path)

        return sorted(files)

    @staticmethod
    def scan_by_pattern(path: str, pattern: str, recursive: bool = True) -> List[str]:
        """Scan directory for files matching pattern."""
        import fnmatch

        files = []

        if recursive:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    if fnmatch.fnmatch(filename, pattern):
                        files.append(os.path.join(root, filename))
        else:
            for item in os.listdir(path):
                if fnmatch.fnmatch(item, pattern):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path):
                        files.append(item_path)

        return sorted(files)

    @staticmethod
    def scan_by_extension(
        path: str, extensions: List[str], recursive: bool = True
    ) -> List[str]:
        """Scan directory for files with specific extensions."""
        files = []
        extensions = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in extensions
        ]

        if recursive:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in extensions):
                        files.append(os.path.join(root, filename))
        else:
            for item in os.listdir(path):
                if any(item.lower().endswith(ext) for ext in extensions):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path):
                        files.append(item_path)

        return sorted(files)

    @staticmethod
    def get_directory_tree(
        path: str, max_depth: Optional[int] = None, include_hidden: bool = False
    ) -> Dict[str, Any]:
        """Get directory tree structure."""

        def build_tree(current_path: str, current_depth: int = 0) -> Dict[str, Any]:
            if max_depth is not None and current_depth > max_depth:
                return {}

            tree = {}

            try:
                items = os.listdir(current_path)
                if not include_hidden:
                    items = [item for item in items if not item.startswith(".")]

                for item in sorted(items):
                    item_path = os.path.join(current_path, item)

                    if os.path.isdir(item_path):
                        tree[item] = {
                            "type": "directory",
                            "children": build_tree(item_path, current_depth + 1),
                        }
                    else:
                        tree[item] = {
                            "type": "file",
                            "size": os.path.getsize(item_path),
                        }
            except PermissionError:
                tree["<permission_denied>"] = {"type": "error"}
            except Exception:
                tree["<error>"] = {"type": "error"}

            return tree

        return build_tree(path)

    @staticmethod
    def get_directory_stats(path: str) -> Dict[str, Any]:
        """Get directory statistics."""
        total_files = 0
        total_dirs = 0
        total_size = 0
        file_types = {}
        extensions = {}

        for root, dirs, files in os.walk(path):
            total_dirs += len(dirs)
            total_files += len(files)

            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    total_size += size

                    # Count file types
                    file_type = FileUtils._detect_file_type(file_path)
                    file_types[file_type.value] = file_types.get(file_type.value, 0) + 1

                    # Count extensions
                    ext = os.path.splitext(file)[1].lower()
                    if ext:
                        extensions[ext] = extensions.get(ext, 0) + 1

                except Exception:
                    pass

        return {
            "total_files": total_files,
            "total_directories": total_dirs,
            "total_size": total_size,
            "total_size_human": FileUtils._format_size(total_size),
            "file_types": file_types,
            "extensions": extensions,
        }
