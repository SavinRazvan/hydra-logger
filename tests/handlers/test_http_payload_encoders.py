"""
Role: Tests for HTTP payload encoder registry and resolution.
Used By:
 - Pytest discovery and CI.
Depends On:
 - hydra_logger.handlers.http_payload_encoders
Notes:
 - Covers register, resolve, unknown name, and clear.
"""

from __future__ import annotations

import pytest

from hydra_logger.handlers.http_payload_encoders import (
    clear_http_payload_encoders,
    register_http_payload_encoder,
    resolve_http_payload_encoder,
    unregister_http_payload_encoder,
)
from hydra_logger.types.records import LogRecord


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    clear_http_payload_encoders()
    yield
    clear_http_payload_encoders()


def _dummy_record() -> LogRecord:
    return LogRecord(
        message="hi",
        level_name="INFO",
        layer="default",
    )


def test_register_and_resolve() -> None:
    def enc(rec: LogRecord, fmt: object) -> dict:
        return {"m": rec.message}

    register_http_payload_encoder("t1", enc)
    fn = resolve_http_payload_encoder("t1")
    assert fn(_dummy_record(), None) == {"m": "hi"}


def test_unknown_encoder_raises() -> None:
    with pytest.raises(ValueError, match="Unknown"):
        resolve_http_payload_encoder("missing")


def test_unregister() -> None:
    register_http_payload_encoder("x", lambda r, f: {})
    unregister_http_payload_encoder("x")
    with pytest.raises(ValueError):
        resolve_http_payload_encoder("x")


def test_load_http_encoders_from_entry_points_noop() -> None:
    from hydra_logger.handlers.http_payload_encoders import (
        load_http_encoders_from_entry_points,
    )

    load_http_encoders_from_entry_points()
