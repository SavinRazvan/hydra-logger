"""
Role: Pytest coverage for configuration defaults and template registry behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates named config resolution and template lifecycle.
"""

import pytest

from hydra_logger.config.configuration_templates import ConfigurationTemplates
from hydra_logger.config.defaults import (
    get_custom_config,
    get_default_config,
    get_named_config,
    get_production_config,
)


def test_default_and_production_configs_return_logging_config() -> None:
    default = get_default_config()
    production = get_production_config()
    assert default.default_level == "INFO"
    assert "default" in default.layers
    assert production.enable_security is True
    assert production.enable_sanitization is True


def test_custom_config_falls_back_to_console_when_no_destination_selected() -> None:
    cfg = get_custom_config(console_enabled=False, file_enabled=False)
    default_destinations = cfg.layers["default"].destinations
    assert len(default_destinations) == 1
    assert default_destinations[0].type == "async_console"


def test_get_named_config_rejects_unknown_name() -> None:
    with pytest.raises(ValueError, match="Unknown configuration name"):
        get_named_config("missing-profile")


def test_get_named_config_logs_unknown_name(caplog) -> None:
    with caplog.at_level("ERROR", logger="hydra_logger.config.defaults"):
        with pytest.raises(ValueError):
            get_named_config("missing-profile")
    assert "Unknown configuration name requested: missing-profile" in caplog.text


def test_template_registry_supports_register_validate_and_cleanup() -> None:
    registry = ConfigurationTemplates()

    @registry.register_template("unit_test_profile", "test profile")
    def _builder():
        return get_default_config()

    assert registry.has_template("unit_test_profile")
    assert registry.validate_template("unit_test_profile") is True
    registry.clear_custom_templates()
    assert not registry.has_template("unit_test_profile")
