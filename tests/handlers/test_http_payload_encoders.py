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
    load_http_encoders_from_entry_points,
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
    load_http_encoders_from_entry_points()


def test_encoder_registry_input_and_overwrite_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        register_http_payload_encoder("   ", lambda _r, _f: {})

    warnings: list[str] = []
    monkeypatch.setattr(
        "hydra_logger.handlers.http_payload_encoders._logger.warning",
        lambda msg, *args: warnings.append(msg % args if args else msg),
    )

    register_http_payload_encoder("dup", lambda _r, _f: {"a": 1})
    register_http_payload_encoder("dup", lambda _r, _f: {"a": 2})
    assert warnings and "Overwriting HTTP payload encoder" in warnings[0]

    assert resolve_http_payload_encoder(None) is None


def test_load_http_encoders_entry_point_error_and_skip_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(
        "hydra_logger.handlers.http_payload_encoders._logger.warning",
        lambda msg, *args: warnings.append(msg % args if args else msg),
    )

    class _BadEp:
        name = "bad"

        @staticmethod
        def load():
            raise RuntimeError("boom")

    class _NonCallableEp:
        name = "obj"

        @staticmethod
        def load():
            return object()

    class _LegacyEps(dict):
        pass

    def _legacy_entry_points():
        eps = _LegacyEps()
        eps["hydra_logger.http_encoders"] = [_BadEp(), _NonCallableEp()]
        return eps

    monkeypatch.setattr("importlib.metadata.entry_points", _legacy_entry_points)
    load_http_encoders_from_entry_points()
    assert any("not callable" in w for w in warnings)
    assert any("Failed to load encoder entry point" in w for w in warnings)

    # Scan failure branch.
    monkeypatch.setattr(
        "importlib.metadata.entry_points",
        lambda: (_ for _ in ()).throw(RuntimeError("scan-fail")),
    )
    load_http_encoders_from_entry_points()


def test_load_http_encoders_registers_callable_entry_point(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _GoodEp:
        name = "good"

        @staticmethod
        def load():
            return lambda rec, _fmt: {"m": rec.message}

    class _LegacyEps(dict):
        pass

    def _legacy_entry_points():
        eps = _LegacyEps()
        eps["hydra_logger.http_encoders"] = [_GoodEp()]
        return eps

    monkeypatch.setattr("importlib.metadata.entry_points", _legacy_entry_points)
    load_http_encoders_from_entry_points()
    fn = resolve_http_payload_encoder("good")
    assert fn(_dummy_record(), None)["m"] == "hi"
