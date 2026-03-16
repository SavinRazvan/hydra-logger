"""
Role: Pytest coverage for record strategy selection behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates profile mapping and strategy edge behavior.
"""

from hydra_logger.types.records import (
    AUTO_CONTEXT_STRATEGY,
    CONTEXT_STRATEGY,
    MINIMAL_STRATEGY,
    RecordCreationStrategy,
    get_record_creation_strategy,
)


def test_get_record_creation_strategy_maps_profiles_and_fallback() -> None:
    assert get_record_creation_strategy("minimal") is MINIMAL_STRATEGY
    assert get_record_creation_strategy("balanced") is CONTEXT_STRATEGY
    assert get_record_creation_strategy("convenient") is AUTO_CONTEXT_STRATEGY
    assert get_record_creation_strategy("unknown-profile") is MINIMAL_STRATEGY


def test_record_creation_strategy_auto_context_creates_valid_record() -> None:
    strategy = RecordCreationStrategy(strategy=RecordCreationStrategy.AUTO_CONTEXT)
    record = strategy.create_record(level="info", message="hello", layer="runtime")
    assert record.level_name == "INFO"
    assert record.level == 20
    assert record.layer == "runtime"
