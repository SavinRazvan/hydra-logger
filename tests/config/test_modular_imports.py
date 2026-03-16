"""
Role: Pytest coverage for modular config import compatibility.
Used By:
 - Pytest discovery and import compatibility validation.
Depends On:
 - hydra_logger
Notes:
 - Ensures new modular config entrypoints preserve existing model identities.
"""

from hydra_logger.config.destinations import LogDestination
from hydra_logger.config.layers import LogLayer
from hydra_logger.config.models import (
    LogDestination as LegacyLogDestination,
    LogLayer as LegacyLogLayer,
    LoggingConfig as LegacyLoggingConfig,
)
from hydra_logger.config.runtime import LoggingConfig
from hydra_logger.config.validation import normalize_level


def test_modular_config_entrypoints_alias_legacy_models() -> None:
    assert LogDestination is LegacyLogDestination
    assert LogLayer is LegacyLogLayer
    assert LoggingConfig is LegacyLoggingConfig


def test_validation_normalize_level() -> None:
    assert normalize_level("info") == "INFO"
