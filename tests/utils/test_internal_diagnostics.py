"""
Role: Pytest coverage for internal diagnostics logger wrappers.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Verifies wrapper functions dispatch to the internal diagnostics logger.
"""

from hydra_logger.utils import internal_diagnostics


def test_internal_diagnostics_wrapper_functions_emit_logs(caplog) -> None:
    with caplog.at_level("DEBUG", logger="hydra_logger.internal"):
        internal_diagnostics.debug("debug event %s", "a")
        internal_diagnostics.info("info event %s", "b")
        internal_diagnostics.warning("warn event %s", "c")
        internal_diagnostics.error("error event %s", "d")

    assert "debug event a" in caplog.text
    assert "info event b" in caplog.text
    assert "warn event c" in caplog.text
    assert "error event d" in caplog.text
