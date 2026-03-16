"""
Role: Regression tests for import-time side effects in public package entrypoints.
Used By:
 - Pytest discovery and runtime safety validation.
Depends On:
 - hydra_logger
 - importlib
Notes:
 - Ensures importing `hydra_logger` does not auto-enable stderr interception.
"""

import importlib

import hydra_logger
from hydra_logger.utils.stderr_interceptor import StderrInterceptor


def test_import_hydra_logger_has_no_stderr_interception_side_effect() -> None:
    """Importing the top-level package must not alter stderr interception state."""
    StderrInterceptor.stop_intercepting()

    importlib.reload(hydra_logger)

    assert StderrInterceptor.is_intercepting() is False
