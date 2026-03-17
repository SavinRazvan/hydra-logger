"""
Role: Pytest coverage for configuration template registry behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates custom template lifecycle and validation pathways.
"""

import pytest

from hydra_logger.config.configuration_templates import ConfigurationTemplates
from hydra_logger.config.models import LogDestination, LogLayer, LoggingConfig
from hydra_logger.core.exceptions import HydraLoggerError


def test_configuration_templates_available_copy_and_custom_clear() -> None:
    templates = ConfigurationTemplates()

    @templates.register_template("custom-x", "x")
    def _custom() -> LoggingConfig:
        return LoggingConfig(
            layers={"default": LogLayer(destinations=[LogDestination(type="console")])}
        )

    available = templates.get_available_templates()
    assert "custom-x" in available
    templates.clear_custom_templates()
    assert templates.has_template("custom-x") is False


def test_configuration_templates_validate_failure_wraps_error() -> None:
    templates = ConfigurationTemplates()

    @templates.register_template("bad-template", "broken")
    def _bad() -> LoggingConfig:
        bad_layer = LogLayer.model_construct(level="INFO", destinations=[])
        return LoggingConfig.model_construct(default_level="INFO", layers={"bad": bad_layer})

    with pytest.raises(
        HydraLoggerError, match="Configuration template validation failed for 'bad-template'"
    ):
        templates.validate_template("bad-template")
