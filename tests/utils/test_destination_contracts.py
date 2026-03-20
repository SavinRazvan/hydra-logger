"""
Role: Contract tests for destination integration messaging.
Used By:
 - CI / pytest for configuration vs runtime alignment.
Depends On:
 - hydra_logger.utils.destination_contracts
Notes:
 - Guards explicit wording for schema-only destination types.
"""

from __future__ import annotations

from hydra_logger.utils.destination_contracts import unsupported_destination_message


def test_async_cloud_message_mentions_schema_and_null_handler() -> None:
    msg = unsupported_destination_message("async_cloud")
    assert "async_cloud" in msg
    assert "schema" in msg.lower()
    assert "NullHandler" in msg


def test_unknown_type_uses_generic_message() -> None:
    msg = unsupported_destination_message("future_sink_xyz")
    assert "future_sink_xyz" in msg
    assert "NullHandler" in msg
