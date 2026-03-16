"""
Role: Pytest coverage for shared logger pipeline services.
Used By:
 - Pytest discovery and pipeline extraction regression checks.
Depends On:
 - hydra_logger
Notes:
 - Validates layer routing fallbacks and dispatch behavior.
"""

from hydra_logger.loggers.pipeline import HandlerDispatcher, LayerRouter


class DummyHandler:
    def __init__(self) -> None:
        self.calls = 0

    def handle(self, _record) -> None:
        self.calls += 1


class DummyLayer:
    def __init__(self, level: str) -> None:
        self.level = level


def test_layer_router_resolves_default_fallback() -> None:
    layers = {"default": DummyLayer("INFO")}
    default_handler = DummyHandler()
    layer_handlers = {"default": [default_handler]}
    router = LayerRouter(layers, layer_handlers, {}, {})

    handlers = router.handlers_for_layer("missing")
    assert handlers == [default_handler]
    assert router.is_level_enabled("missing", 20, "INFO") is True


def test_handler_dispatcher_sync_calls_handle() -> None:
    dispatcher = HandlerDispatcher()
    handler = DummyHandler()
    dispatcher.dispatch_sync(record=object(), handlers=[handler])
    assert handler.calls == 1
