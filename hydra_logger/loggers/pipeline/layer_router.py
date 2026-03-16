"""
Role: Resolve layer handlers and thresholds for logger pipeline.
Used By:
 - `hydra_logger.loggers.sync_logger`
 - `hydra_logger.loggers.async_logger`
Depends On:
 - hydra_logger
 - typing
Notes:
 - Shares layer fallback and level-threshold checks across runtimes.
"""

from typing import Any, Dict, List

from ...types.levels import LogLevelManager


class LayerRouter:
    """Layer routing helper with cache-aware lookups."""

    def __init__(
        self,
        layers: Dict[str, Any],
        layer_handlers: Dict[str, List[Any]],
        handler_cache: Dict[str, List[Any]],
        layer_cache: Dict[str, int],
    ) -> None:
        self._layers = layers
        self._layer_handlers = layer_handlers
        self._handler_cache = handler_cache
        self._layer_cache = layer_cache

    def handlers_for_layer(self, layer_name: str) -> List[Any]:
        """Return handlers for layer using default fallback."""
        if layer_name in self._handler_cache:
            return self._handler_cache[layer_name]

        if layer_name in self._layer_handlers:
            handlers = self._layer_handlers[layer_name]
        elif "default" in self._layer_handlers:
            handlers = self._layer_handlers["default"]
        else:
            handlers = []

        self._handler_cache[layer_name] = handlers
        return handlers

    def layer_threshold(self, layer_name: str, default_level: str) -> int:
        """Resolve numeric threshold for layer with cache fallback."""
        if layer_name in self._layer_cache:
            return self._layer_cache[layer_name]

        if layer_name in self._layers:
            threshold = LogLevelManager.get_level(self._layers[layer_name].level)
        else:
            threshold = LogLevelManager.get_level(default_level)

        self._layer_cache[layer_name] = threshold
        return threshold

    def is_level_enabled(
        self, layer_name: str, level: int, default_level: str = "INFO"
    ) -> bool:
        """Check if level passes layer threshold."""
        return level >= self.layer_threshold(layer_name, default_level)
