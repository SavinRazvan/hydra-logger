"""
Role: Pytest coverage for logger package export wiring.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates `getLogger` factory bridge in `hydra_logger.loggers`.
"""

from hydra_logger import loggers as logger_exports
from hydra_logger.factories import logger_factory


def test_get_logger_delegates_to_factory(monkeypatch) -> None:
    marker = object()

    def fake_create_logger(name=None, **_kwargs):  # type: ignore[no-untyped-def]
        return (name, marker)

    monkeypatch.setattr(logger_factory, "create_logger", fake_create_logger)
    assert logger_exports.getLogger("svc") == ("svc", marker)
