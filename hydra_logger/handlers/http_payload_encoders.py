"""
Role: Registry for named HTTP payload encoders used by network_http handlers.
Used By:
 - hydra_logger.handlers.network_handler and batched HTTP delivery.
Depends On:
 - hydra_logger.types.records
 - importlib.metadata (optional)
Notes:
 - Encoders are registered in Python code or via entry points; YAML references names only.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from ..types.records import LogRecord

_logger = logging.getLogger(__name__)

HttpPayloadEncoder = Callable[[LogRecord, Any], Any]

_HTTP_PAYLOAD_ENCODERS: Dict[str, HttpPayloadEncoder] = {}


def register_http_payload_encoder(name: str, encoder: HttpPayloadEncoder) -> None:
    """
    Register a callable that builds the HTTP body for a log record.

    The encoder receives ``(record, formatter)`` where formatter may be None.
    Return a ``dict`` (JSON body), ``str``, or ``bytes``.
    """
    if not name or not name.strip():
        raise ValueError("Encoder name must be non-empty")
    key = name.strip()
    if key in _HTTP_PAYLOAD_ENCODERS:
        _logger.warning("Overwriting HTTP payload encoder %r", key)
    _HTTP_PAYLOAD_ENCODERS[key] = encoder


def unregister_http_payload_encoder(name: str) -> None:
    """Remove a named encoder (primarily for tests)."""
    _HTTP_PAYLOAD_ENCODERS.pop(name.strip(), None)


def clear_http_payload_encoders() -> None:
    """Clear all registered encoders (primarily for tests)."""
    _HTTP_PAYLOAD_ENCODERS.clear()


def resolve_http_payload_encoder(name: Optional[str]) -> Optional[HttpPayloadEncoder]:
    """Return the encoder callable for name, or None if name is empty/None."""
    if not name:
        return None
    key = name.strip()
    encoder = _HTTP_PAYLOAD_ENCODERS.get(key)
    if encoder is None:
        raise ValueError(
            f"Unknown http_payload_encoder {key!r}; register it with "
            "register_http_payload_encoder or load_http_encoders_from_entry_points"
        )
    return encoder


def load_http_encoders_from_entry_points(
    group: str = "hydra_logger.http_encoders",
) -> None:
    """
    Discover and register encoders from distribution entry points.

    Each entry point name becomes the registry key; the loaded object must be callable.
    """
    try:
        from importlib.metadata import entry_points
    except ImportError:  # pragma: no cover
        return

    try:
        eps = entry_points()
        selected: Any
        if hasattr(eps, "select"):
            selected = eps.select(group=group)
        else:
            legacy_get = getattr(eps, "get", None)
            selected = legacy_get(group) if callable(legacy_get) else ()
    except Exception as exc:  # pragma: no cover - defensive
        _logger.debug("Entry point scan failed: %s", exc)
        return

    for ep in selected:
        try:
            fn = ep.load()
            if not callable(fn):
                _logger.warning("Entry point %s is not callable; skipping", ep.name)
                continue
            register_http_payload_encoder(ep.name, fn)
        except Exception as exc:
            _logger.warning("Failed to load encoder entry point %s: %s", ep.name, exc)
