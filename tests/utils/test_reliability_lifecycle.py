"""
Role: Tests for lifecycle reliability policy helper.
Used By:
 - Pytest discovery and CI policy regression checks.
Depends On:
 - hydra_logger
Notes:
 - Validates raise/warn behavior and failure counter handling.
"""

import pytest

from hydra_logger.core.exceptions import HydraLoggerError
from hydra_logger.utils import reliability_lifecycle


def test_handle_lifecycle_failure_warn_and_raise_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {"count": 0, "last": ""}
    warnings = []

    monkeypatch.setattr(
        "hydra_logger.utils.reliability_lifecycle.diagnostics.warning",
        lambda msg, detail: warnings.append(msg % detail),
    )

    def _inc() -> None:
        state["count"] += 1

    reliability_lifecycle.handle_lifecycle_failure(
        context="close",
        error=RuntimeError("boom"),
        logger_name="unit",
        strict_reliability_mode=False,
        reliability_error_policy="warn",
        failure_warning_interval=1,
        increment_close_failures=_inc,
        get_close_failure_count=lambda: state["count"],
        set_last_error=lambda text: state.__setitem__("last", text),
    )
    assert warnings and "lifecycle failure [close]" in warnings[0]
    assert "lifecycle failure [close]" in state["last"]

    with pytest.raises(HydraLoggerError, match="lifecycle failure"):
        reliability_lifecycle.handle_lifecycle_failure(
            context="close",
            error=RuntimeError("boom"),
            logger_name="unit",
            strict_reliability_mode=True,
            reliability_error_policy="silent",
            failure_warning_interval=100,
            increment_close_failures=_inc,
            get_close_failure_count=lambda: state["count"],
            set_last_error=lambda text: state.__setitem__("last", text),
        )
