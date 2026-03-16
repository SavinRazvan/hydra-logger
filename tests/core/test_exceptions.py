"""
Role: Pytest coverage for core exception behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates detail payload propagation and readable string output.
"""

from hydra_logger.core.exceptions import (
    ConfigurationError,
    FactoryError,
    HandlerError,
    HydraLoggerError,
    ValidationError,
)


def test_hydra_logger_error_string_and_details_roundtrip() -> None:
    err = HydraLoggerError("boom", {"module": "core"})
    assert str(err) == "boom - Details: {'module': 'core'}"
    assert err.get_details() == {"module": "core"}


def test_configuration_and_validation_error_fields() -> None:
    cfg = ConfigurationError("bad config", config_path="cfg.yml")
    val = ValidationError("bad value", field="level", value="TRACE", rule="known_level")
    assert cfg.config_path == "cfg.yml"
    assert val.field == "level"
    assert val.get_details()["rule"] == "known_level"


def test_handler_and_factory_error_include_context() -> None:
    handler_err = HandlerError("handler failed", handler_type="file", operation="emit")
    factory_err = FactoryError(
        "factory failed", component_type="logger", factory_method="create_logger"
    )
    assert "handler_type" in handler_err.get_details()
    assert factory_err.get_details()["factory_method"] == "create_logger"
