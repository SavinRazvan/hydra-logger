"""
Role: Load and validate LoggingConfig from YAML (or JSON) files with optional composition.
Used By:
 - Logger factories and applications using file-based configuration.
Depends On:
 - pathlib
 - hydra_logger.config.models
 - yaml
Notes:
 - Uses ``yaml.safe_load`` only; typical JSON documents parse the same way (same schema as YAML). Supports ``extends``,
   optional cache, and strict top-level keys.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Union, cast

import yaml
from pydantic import BaseModel, ConfigDict

from .models import LoggingConfig

_logger = logging.getLogger(__name__)

_CONFIG_CACHE: Dict[tuple[str, float], LoggingConfig] = {}


class StrictLoggingConfig(LoggingConfig):
    """LoggingConfig variant that rejects unknown top-level keys."""

    model_config = ConfigDict(extra="forbid")


def _count_structure_nodes(obj: Any) -> int:
    """Approximate merged document size for guardrails."""
    if isinstance(obj, dict):
        return 1 + sum(_count_structure_nodes(v) for v in obj.values())
    if isinstance(obj, list):
        return 1 + sum(_count_structure_nodes(v) for v in obj)
    return 1


def _deep_merge_dict(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """Deep-merge dicts; lists and scalars from overlay replace base."""
    result: Dict[str, Any] = dict(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dict(cast(Dict[str, Any], result[key]), value)
        else:
            result[key] = value
    return result


def _normalize_extends(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        out: List[str] = []
        for item in raw:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("extends entries must be non-empty strings")
            out.append(item.strip())
        return out
    raise ValueError("extends must be a string or a list of strings")


def _load_yaml_mapping(path: Path, *, encoding: str) -> Dict[str, Any]:
    text = path.read_text(encoding=encoding)
    loaded = yaml.safe_load(text)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"YAML root must be a mapping, got {type(loaded).__name__}")
    return cast(Dict[str, Any], loaded)


def _merge_extends_chain(
    path: Path,
    *,
    max_depth: int,
    max_merged_nodes: int,
    chain: frozenset[Path],
    encoding: str,
) -> Dict[str, Any]:
    """Load path and merge parent files listed in extends (parents first)."""
    resolved = path.resolve()
    if resolved in chain:
        raise ValueError(f"extends cycle detected involving {resolved}")
    if max_depth < 0:
        raise ValueError(
            f"extends max depth exceeded while loading {resolved}; increase max_extends_depth "
            "or flatten templates"
        )

    data = _load_yaml_mapping(resolved, encoding=encoding)
    extends = data.pop("extends", None)
    parents = _normalize_extends(extends)

    merged: Dict[str, Any] = {}
    next_chain = frozenset(chain | {resolved})
    for parent_rel in parents:
        parent_path = (resolved.parent / parent_rel).resolve()
        parent_data = _merge_extends_chain(
            parent_path,
            max_depth=max_depth - 1,
            max_merged_nodes=max_merged_nodes,
            chain=next_chain,
            encoding=encoding,
        )
        merged = _deep_merge_dict(merged, parent_data)

    merged = _deep_merge_dict(merged, data)
    nodes = _count_structure_nodes(merged)
    if nodes > max_merged_nodes:
        raise ValueError(
            f"Merged YAML from {resolved} exceeds max_merged_nodes={max_merged_nodes} "
            f"(approx nodes={nodes})"
        )
    return merged


def load_logging_config(
    path: Union[str, Path],
    *,
    strict_unknown_fields: bool = False,
    max_extends_depth: int = 5,
    max_merged_nodes: int = 10_000,
    use_config_cache: bool = False,
    encoding: str = "utf-8",
) -> LoggingConfig:
    """
    Load a LoggingConfig from a YAML or JSON file.

    The file may declare ``extends`` (string or list of strings) with paths relative
    to the including file. Parents are merged first; the current file overrides.
    JSON is supported when it parses via ``yaml.safe_load`` (usual ``.json`` configs qualify).

    Args:
        path: Filesystem path to ``.yaml`` / ``.yml`` / ``.json`` (or any text parseable as a mapping).
        strict_unknown_fields: When True, unknown top-level keys raise validation error.
        max_extends_depth: Maximum number of nested extends resolutions.
        max_merged_nodes: Approximate node-count guardrail after merge.
        use_config_cache: Cache by resolved path and mtime (process-local).
        encoding: Text encoding for reading YAML files.

    Returns:
        Validated LoggingConfig instance.
    """
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise FileNotFoundError(f"Logging config not found: {file_path}")

    resolved = str(file_path.resolve())
    mtime = file_path.stat().st_mtime
    cache_key = (resolved, mtime)
    if use_config_cache and cache_key in _CONFIG_CACHE:
        return _CONFIG_CACHE[cache_key]

    merged = _merge_extends_chain(
        file_path,
        max_depth=max_extends_depth,
        max_merged_nodes=max_merged_nodes,
        chain=frozenset(),
        encoding=encoding,
    )

    model_cls: type[BaseModel] = (
        StrictLoggingConfig if strict_unknown_fields else LoggingConfig
    )
    try:
        config = model_cls.model_validate(merged)
    except Exception:
        _logger.exception("Invalid logging configuration in %s", resolved)
        raise

    if not isinstance(config, LoggingConfig):
        raise TypeError("Internal error: validated config is not LoggingConfig")

    if use_config_cache:
        _CONFIG_CACHE[cache_key] = config
    return config


def clear_logging_config_cache() -> None:
    """Clear the process-local config cache used by load_logging_config."""
    _CONFIG_CACHE.clear()
