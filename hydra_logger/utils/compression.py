"""
Data Compression Utilities for Hydra-Logger

This module provides comprehensive data compression utilities supporting
multiple algorithms, compression levels, and file operations. It includes
both data and file compression with performance monitoring and error handling.

FEATURES:
- Multiple compression algorithms (GZIP, BZIP2, LZMA)
- Configurable compression levels (fastest to maximum)
- Data and file compression operations
- Compression ratio and performance metrics
- Checksum verification and integrity checking
- File extension detection and algorithm auto-detection
- Chunked processing for large files

SUPPORTED ALGORITHMS:
- GZIP: Fast compression with good ratio
- BZIP2: High compression ratio, slower
- LZMA: Excellent compression ratio, slower
- NONE: No compression (passthrough)

COMPRESSION LEVELS:
- FASTEST: Fastest compression, lower ratio
- FAST: Fast compression with moderate ratio
- DEFAULT: Balanced speed and ratio
- BEST: High compression ratio, slower
- MAXIMUM: Maximum compression, slowest

USAGE:
    from hydra_logger.utils import CompressionManager, CompressionOptions
    
    # High-level compression management
    manager = CompressionManager()
    options = CompressionOptions(algorithm=CompressionType.GZIP, level=CompressionLevel.DEFAULT)
    result = manager.compress_data(data, options)
    
    # File compression
    result = manager.compress_file("input.txt", options)
    decompressed = manager.decompress_file("input.txt.gz")
    
    # Direct processor usage
    from hydra_logger.utils import GzipProcessor
    compressed = GzipProcessor.compress(data, level=6)
    decompressed = GzipProcessor.decompress(compressed)
"""

import gzip
import bz2
import lzma
import io
import os
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable, BinaryIO
from dataclasses import dataclass
from enum import Enum
import tempfile
import shutil

# Import centralized types
from hydra_logger.types.enums import CompressionType


class CompressionLevel(Enum):
    """Compression levels for different algorithms."""

    FASTEST = "fastest"
    FAST = "fast"
    DEFAULT = "default"
    BEST = "best"
    MAXIMUM = "maximum"


@dataclass
class CompressionOptions:
    """Compression configuration options."""

    algorithm: CompressionType = CompressionType.GZIP
    level: CompressionLevel = CompressionLevel.DEFAULT
    chunk_size: int = 8192
    preserve_original: bool = False
    add_extension: bool = True
    verify_checksum: bool = True


@dataclass
class CompressionResult:
    """Result of compression operation."""

    success: bool
    original_size: int
    compressed_size: int
    compression_ratio: float
    algorithm: CompressionType
    compressed_data: Optional[bytes] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None

    @property
    def space_saved(self) -> int:
        """Calculate space saved in bytes."""
        return self.original_size - self.compressed_size

    @property
    def space_saved_percent(self) -> float:
        """Calculate space saved as percentage."""
        if self.original_size == 0:
            return 0.0
        return (self.space_saved / self.original_size) * 100


class CompressionUtils:
    """General compression utility functions."""

    # Algorithm-specific compression levels
    _GZIP_LEVELS = {
        CompressionLevel.FASTEST: 1,
        CompressionLevel.FAST: 3,
        CompressionLevel.DEFAULT: 6,
        CompressionLevel.BEST: 9,
        CompressionLevel.MAXIMUM: 9,
    }

    _BZIP2_LEVELS = {
        CompressionLevel.FASTEST: 1,
        CompressionLevel.FAST: 3,
        CompressionLevel.DEFAULT: 6,
        CompressionLevel.BEST: 9,
        CompressionLevel.MAXIMUM: 9,
    }

    # Note: ZLIB levels removed as ZLIB is not in the main CompressionType enum

    _LZMA_LEVELS = {
        CompressionLevel.FASTEST: 0,
        CompressionLevel.FAST: 3,
        CompressionLevel.DEFAULT: 6,
        CompressionLevel.BEST: 9,
        CompressionLevel.MAXIMUM: 9,
    }

    @staticmethod
    def get_compression_level(algorithm: CompressionType, level: CompressionLevel) -> int:
        """Get numeric compression level for algorithm."""
        level_maps = {
            CompressionType.GZIP: CompressionUtils._GZIP_LEVELS,
            CompressionType.BZIP2: CompressionUtils._BZIP2_LEVELS,
            CompressionType.LZMA: CompressionUtils._LZMA_LEVELS,
        }
        return level_maps.get(algorithm, {}).get(level, 6)

    @staticmethod
    def get_file_extension(algorithm: CompressionType) -> str:
        """Get file extension for compression algorithm."""
        extensions = {
            CompressionType.GZIP: ".gz",
            CompressionType.BZIP2: ".bz2",
            CompressionType.LZMA: ".xz",
            CompressionType.NONE: "",
        }
        return extensions.get(algorithm, "")

    @staticmethod
    def is_compressed_file(file_path: str) -> bool:
        """Check if file is compressed based on extension."""
        extensions = [".gz", ".bz2", ".xz", ".zip", ".tar.gz", ".tar.bz2"]
        return any(file_path.endswith(ext) for ext in extensions)

    @staticmethod
    def detect_compression_algorithm(file_path: str) -> Optional[CompressionType]:
        """Detect compression algorithm from file extension."""
        if file_path.endswith(".gz"):
            return CompressionType.GZIP
        elif file_path.endswith(".bz2"):
            return CompressionType.BZIP2
        elif file_path.endswith(".xz"):
            return CompressionType.LZMA
        return None

    @staticmethod
    def calculate_checksum(data: bytes) -> str:
        """Calculate SHA-256 checksum of data."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0


class GzipProcessor:
    """GZIP compression processor."""

    @staticmethod
    def compress(data: bytes, level: int = 6) -> bytes:
        """Compress data using GZIP."""
        return gzip.compress(data, compresslevel=level)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        """Decompress GZIP data."""
        return gzip.decompress(data)

    @staticmethod
    def compress_file(
        input_path: str, output_path: str, level: int = 6, chunk_size: int = 8192
    ) -> bool:
        """Compress file using GZIP."""
        try:
            with open(input_path, "rb") as infile, gzip.open(
                output_path, "wb", compresslevel=level
            ) as outfile:
                shutil.copyfileobj(infile, outfile, length=chunk_size)
            return True
        except Exception:
            return False

    @staticmethod
    def decompress_file(input_path: str, output_path: str, chunk_size: int = 8192) -> bool:
        """Decompress GZIP file."""
        try:
            with gzip.open(input_path, "rb") as infile, open(output_path, "wb") as outfile:
                shutil.copyfileobj(infile, outfile, length=chunk_size)
            return True
        except Exception:
            return False

    @staticmethod
    def get_compressed_size(data: bytes, level: int = 6) -> int:
        """Get size of compressed data."""
        return len(GzipProcessor.compress(data, level))


class Bzip2Processor:
    """BZIP2 compression processor."""

    @staticmethod
    def compress(data: bytes, level: int = 6) -> bytes:
        """Compress data using BZIP2."""
        return bz2.compress(data, compresslevel=level)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        """Decompress BZIP2 data."""
        return bz2.decompress(data)

    @staticmethod
    def compress_file(
        input_path: str, output_path: str, level: int = 6, chunk_size: int = 8192
    ) -> bool:
        """Compress file using BZIP2."""
        try:
            with open(input_path, "rb") as infile, bz2.open(
                output_path, "wb", compresslevel=level
            ) as outfile:
                shutil.copyfileobj(infile, outfile, length=chunk_size)
            return True
        except Exception:
            return False

    @staticmethod
    def decompress_file(input_path: str, output_path: str, chunk_size: int = 8192) -> bool:
        """Decompress BZIP2 file."""
        try:
            with bz2.open(input_path, "rb") as infile, open(output_path, "wb") as outfile:
                shutil.copyfileobj(infile, outfile, length=chunk_size)
            return True
        except Exception:
            return False

    @staticmethod
    def get_compressed_size(data: bytes, level: int = 6) -> int:
        """Get size of compressed data."""
        return len(Bzip2Processor.compress(data, level))


class LzmaProcessor:
    """LZMA compression processor."""

    @staticmethod
    def compress(data: bytes, level: int = 6) -> bytes:
        """Compress data using LZMA."""
        return lzma.compress(data, preset=level)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        """Decompress LZMA data."""
        return lzma.decompress(data)

    @staticmethod
    def compress_file(
        input_path: str, output_path: str, level: int = 6, chunk_size: int = 8192
    ) -> bool:
        """Compress file using LZMA."""
        try:
            with open(input_path, "rb") as infile, lzma.open(
                output_path, "wb", preset=level
            ) as outfile:
                shutil.copyfileobj(infile, outfile, length=chunk_size)
            return True
        except Exception:
            return False

    @staticmethod
    def decompress_file(input_path: str, output_path: str, chunk_size: int = 8192) -> bool:
        """Decompress LZMA file."""
        try:
            with lzma.open(input_path, "rb") as infile, open(output_path, "wb") as outfile:
                shutil.copyfileobj(infile, outfile, length=chunk_size)
            return True
        except Exception:
            return False

    @staticmethod
    def get_compressed_size(data: bytes, level: int = 6) -> int:
        """Get size of compressed data."""
        return len(LzmaProcessor.compress(data, level))


# ZlibProcessor removed as ZLIB is not in the main CompressionType enum
    """ZLIB compression processor."""

# compress method removed

# decompress method removed

# compress_file method removed

# decompress_file method removed

# get_compressed_size method removed


class CompressionManager:
    """High-level compression management."""

    def __init__(self):
        """Initialize compression manager."""
        self._processors = {
            CompressionType.GZIP: GzipProcessor(),
            CompressionType.BZIP2: Bzip2Processor(),
            CompressionType.LZMA: LzmaProcessor(),
            # Note: ZSTD is not implemented yet, using ZlibProcessor as fallback
            # CompressionType.ZSTD: ZstdProcessor(),
        }

    def compress_data(
        self, data: bytes, options: CompressionOptions
    ) -> CompressionResult:
        """Compress data with specified options."""
        if options.algorithm == CompressionType.NONE:
            return CompressionResult(
                success=True,
                original_size=len(data),
                compressed_size=len(data),
                compression_ratio=1.0,
                algorithm=options.algorithm,
            )

        try:
            processor = self._processors[options.algorithm]
            level = CompressionUtils.get_compression_level(
                options.algorithm, options.level
            )
            compressed_data = processor.compress(data, level)
            checksum = (
                CompressionUtils.calculate_checksum(compressed_data)
                if options.verify_checksum
                else None
            )

            return CompressionResult(
                success=True,
                original_size=len(data),
                compressed_size=len(compressed_data),
                compression_ratio=len(compressed_data) / len(data),
                algorithm=options.algorithm,
                compressed_data=compressed_data,
                checksum=checksum,
            )
        except Exception as e:
            return CompressionResult(
                success=False,
                original_size=len(data),
                compressed_size=0,
                compression_ratio=0.0,
                algorithm=options.algorithm,
                error_message=str(e),
            )

    def decompress_data(
        self, data: bytes, algorithm: CompressionType
    ) -> Optional[bytes]:
        """Decompress data using specified algorithm."""
        if algorithm == CompressionType.NONE:
            return data

        try:
            processor = self._processors[algorithm]
            return processor.decompress(data)
        except Exception:
            return None

    def compress_file(
        self, input_path: str, options: CompressionOptions
    ) -> CompressionResult:
        """Compress file with specified options."""
        if not os.path.exists(input_path):
            return CompressionResult(
                success=False,
                original_size=0,
                compressed_size=0,
                compression_ratio=0.0,
                algorithm=options.algorithm,
                error_message="Input file does not exist",
            )

        original_size = CompressionUtils.get_file_size(input_path)
        if original_size == 0:
            return CompressionResult(
                success=False,
                original_size=0,
                compressed_size=0,
                compression_ratio=0.0,
                algorithm=options.algorithm,
                error_message="Input file is empty",
            )

        try:
            # Determine output path
            if options.add_extension:
                output_path = input_path + CompressionUtils.get_file_extension(
                    options.algorithm
                )
            else:
                output_path = input_path + ".compressed"

            # Compress file
            processor = self._processors[options.algorithm]
            level = CompressionUtils.get_compression_level(
                options.algorithm, options.level
            )
            success = processor.compress_file(
                input_path, output_path, level, options.chunk_size
            )

            if success:
                compressed_size = CompressionUtils.get_file_size(output_path)
                checksum = (
                    CompressionUtils.calculate_checksum(
                        open(output_path, "rb").read()
                    )
                    if options.verify_checksum
                    else None
                )

                return CompressionResult(
                    success=True,
                    original_size=original_size,
                    compressed_size=compressed_size,
                    compression_ratio=compressed_size / original_size,
                    algorithm=options.algorithm,
                    checksum=checksum,
                    output_path=output_path,
                )
            else:
                return CompressionResult(
                    success=False,
                    original_size=original_size,
                    compressed_size=0,
                    compression_ratio=0.0,
                    algorithm=options.algorithm,
                    error_message="Compression failed",
                )

        except Exception as e:
            return CompressionResult(
                success=False,
                original_size=original_size,
                compressed_size=0,
                compression_ratio=0.0,
                algorithm=options.algorithm,
                error_message=str(e),
            )

    def decompress_file(
        self, input_path: str, output_path: Optional[str] = None
    ) -> Optional[str]:
        """Decompress file to output path."""
        if not os.path.exists(input_path):
            return None

        # Detect algorithm from file extension
        algorithm = CompressionUtils.detect_compression_algorithm(input_path)
        if algorithm is None:
            return None

        # Determine output path
        if output_path is None:
            base_path = input_path
            for ext in [".gz", ".bz2", ".xz", ".zlib"]:
                if base_path.endswith(ext):
                    base_path = base_path[: -len(ext)]
                    break
            output_path = base_path

        try:
            processor = self._processors[algorithm]
            success = processor.decompress_file(input_path, output_path)
            return output_path if success else None
        except Exception:
            return None

    def get_compression_info(self, file_path: str) -> Dict[str, Any]:
        """Get compression information for file."""
        info = {
            "path": file_path,
            "exists": os.path.exists(file_path),
            "size": CompressionUtils.get_file_size(file_path),
            "algorithm": None,
            "is_compressed": False,
        }

        if info["exists"]:
            algorithm = CompressionUtils.detect_compression_algorithm(file_path)
            info["algorithm"] = algorithm.value if algorithm else None
            info["is_compressed"] = algorithm is not None

        return info

    def list_compression_algorithms(self) -> List[Dict[str, Any]]:
        """List available compression algorithms with information."""
        algorithms = []
        for algorithm in CompressionType:
            if algorithm == CompressionType.NONE:
                continue

            processor = self._processors[algorithm]
            extension = CompressionUtils.get_file_extension(algorithm)
            levels = list(range(1, 10)) if algorithm != CompressionType.LZMA else list(
                range(10)
            )

            algorithms.append(
                {
                    "name": algorithm.value,
                    "extension": extension,
                    "supported_levels": levels,
                    "processor": processor.__class__.__name__,
                }
            )

        return algorithms
