"""
Serialization Utilities for Hydra-Logger

This module provides comprehensive serialization utilities supporting multiple
formats including JSON, YAML, TOML, Pickle, and MessagePack. It includes
both high-level and format-specific processors with compression support.

FEATURES:
- SerializationUtils: High-level serialization management
- Format-specific processors (JSON, YAML, TOML, Pickle, MessagePack)
- Compression integration for efficient storage
- File and stream serialization support
- Format detection and validation
- Error handling and fallback mechanisms
- Performance optimization and caching

SUPPORTED FORMATS:
- JSON: Human-readable, widely supported
- YAML: Human-readable, configuration-friendly
- TOML: Simple configuration format
- Pickle: Python-native binary format
- MessagePack: Compact binary format
- Binary: Raw binary serialization

SERIALIZATION FEATURES:
- Data serialization and deserialization
- File-based serialization operations
- Stream-based processing
- Format validation and error checking
- Compression integration
- Custom serialization options

USAGE:
    from hydra_logger.utils import SerializationUtils, SerializationOptions
    
    # High-level serialization
    options = SerializationOptions(format=SerializationFormat.JSON, indent=2)
    serialized = SerializationUtils.serialize(data, options)
    deserialized = SerializationUtils.deserialize(serialized, options)
    
    # Format-specific processors
    from hydra_logger.utils import JSONProcessor, YAMLProcessor
    json_str = JSONProcessor.serialize(data, indent=2)
    yaml_str = YAMLProcessor.serialize(data, default_flow_style=False)
    
    # File operations
    success = JSONProcessor.serialize_to_file(data, "output.json")
    data = JSONProcessor.deserialize_from_file("input.json")
    
    # Stream processing
    JSONProcessor.serialize_stream(data, open("output.json", "w"))
    data = JSONProcessor.deserialize_stream(open("input.json", "r"))

The module also provides utilities for compressing and decompressing data.

The module also provides utilities for detecting the serialization format of data.

The module also provides utilities for validating data.
"""

import json
import pickle
import yaml
import toml
from typing import Any, List, Optional, Union, BinaryIO, TextIO, Callable
from dataclasses import dataclass
from enum import Enum

# Import centralized types
from hydra_logger.types.enums import CompressionType


class SerializationFormat(Enum):
    """Supported serialization formats."""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    PICKLE = "pickle"
    MESSAGEPACK = "messagepack"
    BINARY = "binary"


# CompressionType is now imported from types.enums


@dataclass
class SerializationOptions:
    """Serialization configuration options."""

    format: SerializationFormat = SerializationFormat.JSON
    compression: CompressionType = CompressionType.NONE
    encoding: str = "utf-8"
    indent: Optional[int] = None
    sort_keys: bool = False
    ensure_ascii: bool = False
    default: Optional[Callable] = None
    separators: Optional[tuple] = None
    skipkeys: bool = False
    allow_nan: bool = True
    cls: Optional[type] = None


class SerializationUtils:
    """General serialization utilities."""

    @staticmethod
    def serialize(data: Any, options: SerializationOptions) -> Union[str, bytes]:
        """Serialize data according to options."""
        if options.format == SerializationFormat.JSON:
            serialized = SerializationUtils._serialize_json(data, options)
        elif options.format == SerializationFormat.YAML:
            serialized = SerializationUtils._serialize_yaml(data, options)
        elif options.format == SerializationFormat.TOML:
            serialized = SerializationUtils._serialize_toml(data, options)
        elif options.format == SerializationFormat.PICKLE:
            serialized = SerializationUtils._serialize_pickle(data, options)
        elif options.format == SerializationFormat.MESSAGEPACK:
            serialized = SerializationUtils._serialize_messagepack(
                data, options
            )
        else:
            raise ValueError(f"Unsupported serialization format: {options.format}")

        # Apply compression if specified
        if options.compression != CompressionType.NONE:
            # Use compression manager for compression
            from hydra_logger.utils.compression import CompressionManager, CompressionOptions
            compression_manager = CompressionManager()
            if isinstance(serialized, str):
                serialized = serialized.encode('utf-8')
            
            # Create compression options with default level
            from hydra_logger.utils.compression import CompressionLevel
            compression_options = CompressionOptions(algorithm=options.compression, level=CompressionLevel.DEFAULT)
            
            # Compress the data
            result = compression_manager.compress_data(serialized, compression_options)
            if result.success:
                serialized = result.compressed_data
            else:
                # If compression fails, log warning but continue without compression
                import logging
                logging.warning(f"Compression failed: {result.error_message}")

        return serialized

    @staticmethod
    def deserialize(data: Union[str, bytes], options: SerializationOptions) -> Any:
        """Deserialize data according to options."""
        # Decompress if compressed
        if options.compression != CompressionType.NONE:
            # Use compression manager for decompression
            from hydra_logger.utils.compression import CompressionManager
            compression_manager = CompressionManager()
            decompressed = compression_manager.decompress_data(
                data, options.compression
            )
            if decompressed is not None:
                data = decompressed
            else:
                # If decompression fails, log warning but continue
                import logging
                logging.warning(f"Decompression failed for {options.compression}")

        if options.format == SerializationFormat.JSON:
            return SerializationUtils._deserialize_json(data, options)
        elif options.format == SerializationFormat.YAML:
            return SerializationUtils._deserialize_yaml(
                data, options
            )
        elif options.format == SerializationFormat.TOML:
            return SerializationUtils._deserialize_toml(
                data, options
            )
        elif options.format == SerializationFormat.PICKLE:
            return SerializationUtils._deserialize_pickle(
                data, options
            )
        elif options.format == SerializationFormat.MESSAGEPACK:
            return SerializationUtils._deserialize_messagepack(
                data, options
            )
        else:
            raise ValueError(f"Unsupported serialization format: {options.format}")

    @staticmethod
    def _serialize_json(data: Any, options: SerializationOptions) -> str:
        """Serialize data to JSON."""
        kwargs = {}
        if options.indent is not None:
            kwargs['indent'] = options.indent
        if options.sort_keys:
            kwargs['sort_keys'] = True
        if options.ensure_ascii is not None:
            kwargs['ensure_ascii'] = options.ensure_ascii
        if options.default:
            kwargs['default'] = options.default
        if options.separators:
            kwargs['separators'] = options.separators
        if options.skipkeys:
            kwargs['skipkeys'] = True
        if options.allow_nan is not None:
            kwargs['allow_nan'] = options.allow_nan
        if options.cls:
            kwargs['cls'] = options.cls

        return json.dumps(data, **kwargs)

    @staticmethod
    def _deserialize_json(
        data: Union[str, bytes], options: SerializationOptions
    ) -> Any:
        """Deserialize data from JSON."""
        if isinstance(data, bytes):
            data = data.decode(
                options.encoding
            )

        kwargs = {}
        if options.cls:
            kwargs['cls'] = options.cls

        return json.loads(data, **kwargs)

    @staticmethod
    def _serialize_yaml(data: Any, options: SerializationOptions) -> str:
        """Serialize data to YAML."""
        kwargs = {}
        if options.default:
            kwargs['default_flow_style'] = False
            kwargs['allow_unicode'] = True

        return yaml.dump(data, **kwargs)

    @staticmethod
    def _deserialize_yaml(
        data: Union[str, bytes], options: SerializationOptions
    ) -> Any:
        """Deserialize data from YAML."""
        if isinstance(data, bytes):
            data = data.decode(
                options.encoding
            )

        return yaml.safe_load(data)

    @staticmethod
    def _serialize_toml(data: Any, options: SerializationOptions) -> str:
        """Serialize data to TOML."""
        return toml.dump(data)

    @staticmethod
    def _deserialize_toml(
        data: Union[str, bytes], options: SerializationOptions
    ) -> Any:
        """Deserialize data from TOML."""
        if isinstance(data, bytes):
            data = data.decode(
                options.encoding
            )

        return toml.loads(data)

    @staticmethod
    def _serialize_pickle(data: Any, options: SerializationOptions) -> bytes:
        """Serialize data to pickle."""
        return pickle.dumps(data)

    @staticmethod
    def _deserialize_pickle(
        data: Union[str, bytes], options: SerializationOptions
    ) -> Any:
        """Deserialize data from pickle."""
        if isinstance(data, str):
            data = data.encode(
                options.encoding
            )

        return pickle.loads(data)

    @staticmethod
    def _serialize_messagepack(
        data: Any, options: SerializationOptions
    ) -> bytes:
        """Serialize data to MessagePack."""
        try:
            import msgpack  # noqa: F401
            return msgpack.packb(data)
        except ImportError:
            raise ImportError(
                "MessagePack not available. Install with: pip install msgpack"
            )

    @staticmethod
    def _deserialize_messagepack(
        data: Union[str, bytes], options: SerializationOptions
    ) -> Any:
        """Deserialize data from MessagePack."""
        try:
            import msgpack  # noqa: F401
            if isinstance(data, str):
                data = data.encode(options.encoding)
            return msgpack.unpackb(data)
        except ImportError:
            raise ImportError(
                "MessagePack not available. Install with: pip install msgpack"
            )

    # Compression methods are now handled by the dedicated compression module
    # Import and use CompressionManager from hydra_logger.utils.compression

    @staticmethod
    def detect_format(data: Union[str, bytes]) -> SerializationFormat:
        """Detect the serialization format of data."""
        if isinstance(data, bytes):
            # Try to detect binary formats
            if data.startswith(b'\x1f\x8b'):  # Gzip
                return SerializationFormat.BINARY
            elif data.startswith(b'BZ'):  # Bzip2
                return SerializationFormat.BINARY
            elif data.startswith(b'\xfd7zXZ'):  # LZMA
                return SerializationFormat.BINARY
            elif data.startswith(b'\x82'):  # MessagePack
                return SerializationFormat.MESSAGEPACK
            else:
                # Try to decode as text
                try:
                    data = data.decode('utf-8')
                except UnicodeDecodeError:
                    return SerializationFormat.PICKLE

        if isinstance(data, str):
            data = data.strip()

            if data.startswith('{') and data.endswith('}'):
                return SerializationFormat.JSON
            elif data.startswith('[') and data.endswith(']'):
                return SerializationFormat.JSON
            elif data.startswith('---') or ':' in data:
                return SerializationFormat.YAML
            elif '=' in data and '\n' in data:
                return SerializationFormat.TOML
            else:
                return SerializationFormat.JSON

        return SerializationFormat.UNKNOWN


class JSONProcessor:
    """JSON-specific serialization utilities."""

    @staticmethod
    def serialize(data: Any, **kwargs) -> str:
        """Serialize data to JSON string."""
        return json.dumps(data, **kwargs)

    @staticmethod
    def deserialize(data: Union[str, bytes], **kwargs) -> Any:
        """Deserialize data from JSON string."""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data, **kwargs)

    @staticmethod
    def serialize_to_file(data: Any, file_path: str, **kwargs) -> bool:
        """Serialize data to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, **kwargs)
            return True
        except Exception:
            return False

    @staticmethod
    def deserialize_from_file(file_path: str, **kwargs) -> Any:
        """Deserialize data from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f, **kwargs)

    @staticmethod
    def serialize_stream(data: Any, stream: TextIO, **kwargs) -> None:
        """Serialize data to JSON stream."""
        json.dump(data, stream, **kwargs)

    @staticmethod
    def deserialize_stream(stream: TextIO, **kwargs) -> Any:
        """Deserialize data from JSON stream."""
        return json.load(stream, **kwargs)

    @staticmethod
    def pretty_print(data: Any, indent: int = 2) -> str:
        """Pretty print JSON data."""
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @staticmethod
    def compact_print(data: Any) -> str:
        """Compact print JSON data."""
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)

    @staticmethod
    def validate_json(data: str) -> bool:
        """Validate JSON string."""
        try:
            json.loads(data)
            return True
        except json.JSONDecodeError:
            return False

    @staticmethod
    def get_json_errors(data: str) -> List[str]:
        """Get JSON parsing errors."""
        try:
            json.loads(data)
            return []
        except json.JSONDecodeError as e:
            return [str(e)]


class YAMLProcessor:
    """YAML-specific serialization utilities."""

    @staticmethod
    def serialize(data: Any, **kwargs) -> str:
        """Serialize data to YAML string."""
        return yaml.dump(data, **kwargs)

    @staticmethod
    def deserialize(data: Union[str, bytes], **kwargs) -> Any:
        """Deserialize data from YAML string."""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return yaml.safe_load(data)

    @staticmethod
    def serialize_to_file(data: Any, file_path: str, **kwargs) -> bool:
        """Serialize data to YAML file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, **kwargs)
            return True
        except Exception:
            return False

    @staticmethod
    def deserialize_from_file(file_path: str, **kwargs) -> Any:
        """Deserialize data from YAML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @staticmethod
    def serialize_stream(data: Any, stream: TextIO, **kwargs) -> None:
        """Serialize data to YAML stream."""
        yaml.dump(data, stream, **kwargs)

    @staticmethod
    def deserialize_stream(stream: TextIO, **kwargs) -> Any:
        """Deserialize data from YAML stream."""
        return yaml.safe_load(stream)

    @staticmethod
    def safe_serialize(data: Any, **kwargs) -> str:
        """Safely serialize data to YAML."""
        kwargs.setdefault('default_flow_style', False)
        kwargs.setdefault('allow_unicode', True)
        return yaml.dump(data, **kwargs)

    @staticmethod
    def validate_yaml(data: str) -> bool:
        """Validate YAML string."""
        try:
            yaml.safe_load(data)
            return True
        except yaml.YAMLError:
            return False


class TOMLProcessor:
    """TOML-specific serialization utilities."""

    @staticmethod
    def serialize(data: Any, **kwargs) -> str:
        """Serialize data to TOML string."""
        return toml.dumps(data)

    @staticmethod
    def deserialize(data: Union[str, bytes], **kwargs) -> Any:
        """Deserialize data from TOML string."""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return toml.loads(data)

    @staticmethod
    def serialize_to_file(data: Any, file_path: str, **kwargs) -> bool:
        """Serialize data to TOML file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                toml.dump(data, f)
            return True
        except Exception:
            return False

    @staticmethod
    def deserialize_from_file(file_path: str, **kwargs) -> Any:
        """Deserialize data from TOML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return toml.load(f)

    @staticmethod
    def validate_toml(data: str) -> bool:
        """Validate TOML string."""
        try:
            toml.loads(data)
            return True
        except toml.TomlDecodeError:
            return False


class PickleProcessor:
    """Pickle-specific serialization utilities."""

    @staticmethod
    def serialize(data: Any, **kwargs) -> bytes:
        """Serialize data to pickle bytes."""
        return pickle.dumps(data, **kwargs)

    @staticmethod
    def deserialize(data: Union[str, bytes], **kwargs) -> Any:
        """Deserialize data from pickle bytes."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return pickle.loads(data)

    @staticmethod
    def serialize_to_file(data: Any, file_path: str, **kwargs) -> bool:
        """Serialize data to pickle file."""
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(data, f, **kwargs)
            return True
        except Exception:
            return False

    @staticmethod
    def deserialize_from_file(file_path: str, **kwargs) -> Any:
        """Deserialize data from pickle file."""
        with open(file_path, 'rb') as f:
            return pickle.load(f)

    @staticmethod
    def serialize_stream(data: Any, stream: BinaryIO, **kwargs) -> None:
        """Serialize data to pickle stream."""
        pickle.dump(data, stream, **kwargs)

    @staticmethod
    def deserialize_stream(stream: BinaryIO, **kwargs) -> Any:
        """Deserialize data from pickle stream."""
        return pickle.load(stream)

    @staticmethod
    def safe_serialize(data: Any, **kwargs) -> bytes:
        """Safely serialize data to pickle."""
        kwargs.setdefault('protocol', pickle.HIGHEST_PROTOCOL)
        return pickle.dumps(data, **kwargs)

    @staticmethod
    def get_pickle_size(data: Any) -> int:
        """Get size of pickled data in bytes."""
        return len(pickle.dumps(data))


class MessagePackProcessor:
    """MessagePack-specific serialization utilities."""

    @staticmethod
    def serialize(data: Any, **kwargs) -> bytes:
        """Serialize data to MessagePack bytes."""
        try:
            import msgpack
            return msgpack.packb(data, **kwargs)
        except ImportError:
            raise ImportError(
                "MessagePack not available. Install with: pip install msgpack"
            )

    @staticmethod
    def deserialize(data: Union[str, bytes], **kwargs) -> Any:
        """Deserialize data from MessagePack bytes."""
        try:
            import msgpack
            if isinstance(data, str):
                data = data.encode('utf-8')
            return msgpack.unpackb(data, **kwargs)
        except ImportError:
            raise ImportError(
                "MessagePack not available. Install with: pip install msgpack"
            )

    @staticmethod
    def serialize_to_file(data: Any, file_path: str, **kwargs) -> bool:
        """Serialize data to MessagePack file."""
        try:
            import msgpack  # noqa: F401
            with open(file_path, 'wb') as f:
                msgpack.pack(data, f, **kwargs)
            return True
        except Exception:
            return False

    @staticmethod
    def deserialize_from_file(file_path: str, **kwargs) -> Any:
        """Deserialize data from MessagePack file."""
        try:
            import msgpack  # noqa: F401
            with open(file_path, 'rb') as f:
                return msgpack.unpack(f, **kwargs)
        except ImportError:
            raise ImportError(
                "MessagePack not available. Install with: pip install msgpack"
            )

    @staticmethod
    def get_messagepack_size(data: Any) -> int:
        """Get size of MessagePack data in bytes."""
        try:
            import msgpack  # noqa: F401
            return len(msgpack.packb(data))
        except ImportError:
            raise ImportError(
                "MessagePack not available. Install with: pip install msgpack"
            )

    @staticmethod
    def is_available() -> bool:
        """Check if MessagePack is available."""
        try:
            import msgpack  # noqa: F401
            return True
        except ImportError:
            return False


# Utility functions for common operations
def serialize_to_json(data: Any, **kwargs) -> str:
    """Quick JSON serialization."""
    return JSONProcessor.serialize(data, **kwargs)


def deserialize_from_json(data: Union[str, bytes], **kwargs) -> Any:
    """Quick JSON deserialization."""
    return JSONProcessor.deserialize(data, **kwargs)


def serialize_to_yaml(data: Any, **kwargs) -> str:
    """Quick YAML serialization."""
    return YAMLProcessor.serialize(data, **kwargs)


def deserialize_from_yaml(data: Union[str, bytes], **kwargs) -> Any:
    """Quick YAML deserialization."""
    return YAMLProcessor.deserialize(data, **kwargs)


def serialize_to_toml(data: Any, **kwargs) -> str:
    """Quick TOML serialization."""
    return TOMLProcessor.serialize(data, **kwargs)


def deserialize_from_toml(data: Union[str, bytes], **kwargs) -> Any:
    """Quick TOML deserialization."""
    return TOMLProcessor.deserialize(data, **kwargs)


def serialize_to_pickle(data: Any, **kwargs) -> bytes:
    """Quick pickle serialization."""
    return PickleProcessor.serialize(data, **kwargs)


def deserialize_from_pickle(data: Union[str, bytes], **kwargs) -> Any:
    """Quick pickle deserialization."""
    return PickleProcessor.deserialize(data, **kwargs)


def serialize_to_messagepack(data: Any, **kwargs) -> bytes:
    """Quick MessagePack serialization."""
    return MessagePackProcessor.serialize(data, **kwargs)


def deserialize_from_messagepack(data: Union[str, bytes], **kwargs) -> Any:
    """Quick MessagePack deserialization."""
    return MessagePackProcessor.deserialize(data, **kwargs)
