"""
Role: Human-readable contract strings for configuration vs runtime handler gaps.
Used By:
 - Sync and async loggers when a destination type has no core handler.
Depends On:
 -
Notes:
 - Keeps integration-point messaging consistent across logger implementations.
"""

from __future__ import annotations

# Destination types accepted by schema/models but without a built-in hydra_logger handler.
_INTEGRATION_POINT_TYPES: frozenset[str] = frozenset({"async_cloud"})


def unsupported_destination_message(dest_type: str) -> str:
    """
    Explain why a destination resolves to NullHandler.

    Args:
        dest_type: LogDestination.type value.
    """
    if dest_type in _INTEGRATION_POINT_TYPES:
        return (
            f"Destination type {dest_type!r} is valid in configuration schema but "
            "has no built-in core handler (integration-point); records are dropped "
            "via NullHandler until a custom handler or adapter is wired."
        )
    return (
        f"No handler implementation for destination type {dest_type!r}; "
        "using NullHandler (records are dropped)."
    )
