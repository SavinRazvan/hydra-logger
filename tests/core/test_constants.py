"""
Role: Pytest coverage for core constant helpers.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Exercises ANSI color lookup and default layer color mapping.
"""

from hydra_logger.core.constants import Colors


def test_ansi_colors_lookup_and_fallback() -> None:
    assert Colors.get_color_code("red") == Colors.RED
    assert Colors.get_color_code("not-a-color") == Colors.WHITE


def test_ansi_layer_color_mapping_defaults() -> None:
    assert Colors.get_layer_color("api")
    assert Colors.get_layer_color("unknown-layer") == Colors.WHITE
