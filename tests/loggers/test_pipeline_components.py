"""
Role: Pytest coverage for extracted logger pipeline components.
Used By:
 - Pytest discovery and architecture regression validation.
Depends On:
 - hydra_logger
 - pytest
Notes:
 - Covers happy path, failure isolation, and async dispatch behavior.
"""

import asyncio
from types import SimpleNamespace

import pytest

from hydra_logger.loggers.pipeline import (
    ComponentDispatcher,
    ExtensionProcessor,
    HandlerDispatcher,
    RecordBuilder,
)
from hydra_logger.types.levels import LogLevelManager


class DummyLogger:
    def __init__(self) -> None:
        self.calls = []

    def create_log_record(self, level, message, **kwargs):
        self.calls.append((level, message, kwargs))
        return {"level": level, "message": message, "kwargs": kwargs}


class HandleOnlyHandler:
    def __init__(self) -> None:
        self.calls = 0

    def handle(self, _record) -> None:
        self.calls += 1


class EmitOnlyHandler:
    def __init__(self) -> None:
        self.calls = 0

    def emit(self, _record) -> None:
        self.calls += 1


class HandleAndEmitHandler:
    def __init__(self) -> None:
        self.handled = 0
        self.emitted = 0

    def handle(self, _record) -> None:
        self.handled += 1

    def emit(self, _record) -> None:
        self.emitted += 1


class FailingHandleHandler:
    def __init__(self) -> None:
        self.calls = 0

    def handle(self, _record) -> None:
        self.calls += 1
        raise RuntimeError("intentional handler failure")


class AsyncEmitHandler:
    def __init__(self) -> None:
        self.calls = 0

    async def emit_async(self, _record) -> None:
        self.calls += 1


class AsyncEmitMethodHandler:
    def __init__(self) -> None:
        self.calls = 0

    async def emit(self, _record) -> None:
        self.calls += 1


class SyncEmitOnlyHandler:
    def __init__(self) -> None:
        self.calls = 0

    def emit(self, _record) -> None:
        self.calls += 1


class FailingAsyncEmitMethodHandler:
    async def emit(self, _record) -> None:
        raise RuntimeError("async emit fail")


class DummyDataProtection:
    def __init__(self, enabled: bool = True, should_fail: bool = False) -> None:
        self._enabled = enabled
        self._should_fail = should_fail
        self.calls = 0

    def is_enabled(self) -> bool:
        return self._enabled

    def process(self, message: str) -> str:
        self.calls += 1
        if self._should_fail:
            raise RuntimeError("process failed")
        return f"masked:{message}"


class SyncComponent:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls = []

    def log(self, level, message, **kwargs) -> None:
        if self.should_fail:
            raise RuntimeError("component failure")
        self.calls.append((level, message, kwargs))


class AsyncComponent:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls = []

    async def log(self, level, message, **kwargs) -> None:
        if self.should_fail:
            raise RuntimeError("component failure")
        self.calls.append((level, message, kwargs))


def test_record_builder_normalizes_level_and_delegates_create() -> None:
    logger = DummyLogger()
    builder = RecordBuilder(logger)

    assert builder.normalize_level("INFO") == LogLevelManager.get_level("INFO")
    assert builder.normalize_level(30) == 30

    record = builder.create("WARNING", "hello", context={"req_id": "x1"})
    assert record["level"] == LogLevelManager.get_level("WARNING")
    assert logger.calls == [
        (
            LogLevelManager.get_level("WARNING"),
            "hello",
            {"context": {"req_id": "x1"}},
        )
    ]


def test_record_builder_logs_and_raises_on_invalid_level(caplog) -> None:
    logger = DummyLogger()
    builder = RecordBuilder(logger)

    with caplog.at_level(
        "ERROR", logger="hydra_logger.loggers.pipeline.record_builder"
    ):
        with pytest.raises(Exception):
            builder.create(object(), "hello")

    assert "Record level normalization failed for level=" in caplog.text


def test_handler_dispatcher_sync_prefers_handle_then_tolerates_failure() -> None:
    dispatcher = HandlerDispatcher()
    first = HandleAndEmitHandler()
    failing = FailingHandleHandler()
    last = EmitOnlyHandler()

    dispatcher.dispatch_sync(
        record=object(),
        handlers=[first, failing, last],
    )

    assert first.handled == 1
    assert first.emitted == 0
    assert failing.calls == 1
    assert last.calls == 1


def test_handler_dispatcher_sync_logs_failure_context(caplog) -> None:
    dispatcher = HandlerDispatcher()
    failing = FailingHandleHandler()

    with caplog.at_level(
        "ERROR", logger="hydra_logger.loggers.pipeline.handler_dispatcher"
    ):
        dispatcher.dispatch_sync(record=object(), handlers=[failing])

    assert (
        "Sync handler dispatch failed for handler type=FailingHandleHandler"
        in caplog.text
    )


def test_handler_dispatcher_async_supports_mixed_handler_shapes() -> None:
    dispatcher = HandlerDispatcher()
    async_emit = AsyncEmitHandler()
    sync_handle = HandleOnlyHandler()
    async_emit_method = AsyncEmitMethodHandler()

    asyncio.run(
        dispatcher.dispatch_async(
            record=object(),
            handlers=[async_emit, sync_handle, async_emit_method],
        )
    )

    assert async_emit.calls == 1
    assert sync_handle.calls == 1
    assert async_emit_method.calls == 1


def test_handler_dispatcher_async_supports_sync_emit_fallback() -> None:
    dispatcher = HandlerDispatcher()
    sync_emit = SyncEmitOnlyHandler()
    asyncio.run(dispatcher.dispatch_async(record=object(), handlers=[sync_emit]))
    assert sync_emit.calls == 1


def test_handler_dispatcher_async_logs_failure_context(caplog) -> None:
    dispatcher = HandlerDispatcher()
    bad = FailingAsyncEmitMethodHandler()

    with caplog.at_level(
        "ERROR", logger="hydra_logger.loggers.pipeline.handler_dispatcher"
    ):
        asyncio.run(dispatcher.dispatch_async(record=object(), handlers=[bad]))

    assert (
        "Async handler dispatch failed for handler type=FailingAsyncEmitMethodHandler"
        in caplog.text
    )


def test_handler_dispatcher_async_noop_handler_shape_and_token_fallback() -> None:
    dispatcher = HandlerDispatcher()

    class NoDispatchMethods:
        pass

    # Cover callable token fallback branch (non-None, non-bound method).
    assert (
        dispatcher._callable_token(lambda: None) != 0
    )  # pylint: disable=protected-access

    # Cover default async dispatch branch that returns noop coroutine.
    asyncio.run(
        dispatcher.dispatch_async(record=object(), handlers=[NoDispatchMethods()])
    )


def test_extension_processor_applies_enabled_protection_only() -> None:
    processor = ExtensionProcessor()
    record = SimpleNamespace(message="secret")

    disabled = DummyDataProtection(enabled=False)
    same_record = processor.apply_data_protection(record, disabled)
    assert same_record.message == "secret"
    assert disabled.calls == 0

    enabled = DummyDataProtection(enabled=True)
    updated_record = processor.apply_data_protection(record, enabled)
    assert updated_record.message == "masked:secret"
    assert enabled.calls == 1


def test_extension_processor_swallows_extension_failures() -> None:
    processor = ExtensionProcessor()
    record = SimpleNamespace(message="secret")
    protection = DummyDataProtection(enabled=True, should_fail=True)

    updated = processor.apply_data_protection(record, protection)
    assert updated.message == "secret"
    assert protection.calls == 1


def test_extension_processor_logs_extension_failures(caplog) -> None:
    processor = ExtensionProcessor()
    record = SimpleNamespace(message="secret")
    protection = DummyDataProtection(enabled=True, should_fail=True)

    with caplog.at_level(
        "ERROR", logger="hydra_logger.loggers.pipeline.extension_processor"
    ):
        processor.apply_data_protection(record, protection)

    assert (
        "Data protection extension failed for type=DummyDataProtection" in caplog.text
    )


def test_extension_processor_applies_data_protection_to_context_and_extra() -> None:
    class MappingProtection:
        @staticmethod
        def is_enabled() -> bool:
            return True

        def process(self, payload):  # type: ignore[no-untyped-def]
            if isinstance(payload, str):
                return payload.replace("token=abc", 'token="[REDACTED]"')
            if isinstance(payload, dict):
                return {
                    key: (
                        self.process(value) if isinstance(value, (dict, str)) else value
                    )
                    for key, value in payload.items()
                }
            return payload

    processor = ExtensionProcessor()
    record = SimpleNamespace(
        message="hello token=abc",
        context={"auth": {"detail": "token=abc"}},
        extra={"password": "token=abc"},
    )
    updated = processor.apply_data_protection(record, MappingProtection())
    assert 'token="[REDACTED]"' in updated.message
    assert updated.context["auth"]["detail"] == 'token="[REDACTED]"'
    assert updated.extra["password"] == 'token="[REDACTED]"'


def test_component_dispatcher_sync_fanout_tolerates_component_failure() -> None:
    dispatcher = ComponentDispatcher()
    ok = SyncComponent()
    bad = SyncComponent(should_fail=True)
    second_ok = SyncComponent()

    dispatcher.dispatch_sync(
        components=[ok, bad, second_ok],
        level="INFO",
        message="fanout",
        request_id="r-1",
    )

    assert ok.calls == [("INFO", "fanout", {"request_id": "r-1"})]
    assert second_ok.calls == [("INFO", "fanout", {"request_id": "r-1"})]


def test_component_dispatcher_sync_logs_component_failure(caplog) -> None:
    dispatcher = ComponentDispatcher()
    bad = SyncComponent(should_fail=True)

    with caplog.at_level(
        "ERROR", logger="hydra_logger.loggers.pipeline.component_dispatcher"
    ):
        dispatcher.dispatch_sync(components=[bad], level="INFO", message="fanout")

    assert (
        "Sync component dispatch failed for component type=SyncComponent" in caplog.text
    )


def test_component_dispatcher_async_mixed_components_and_failure() -> None:
    dispatcher = ComponentDispatcher()
    async_ok = AsyncComponent()
    async_bad = AsyncComponent(should_fail=True)
    sync_ok = SyncComponent()

    asyncio.run(
        dispatcher.dispatch_async(
            components=[async_ok, async_bad, sync_ok],
            level="ERROR",
            message="fanout-async",
            request_id="r-2",
        )
    )

    assert async_ok.calls == [("ERROR", "fanout-async", {"request_id": "r-2"})]
    assert sync_ok.calls == [("ERROR", "fanout-async", {"request_id": "r-2"})]


def test_component_dispatcher_async_logs_component_failure(caplog) -> None:
    dispatcher = ComponentDispatcher()
    bad = AsyncComponent(should_fail=True)

    with caplog.at_level(
        "ERROR", logger="hydra_logger.loggers.pipeline.component_dispatcher"
    ):
        asyncio.run(
            dispatcher.dispatch_async(
                components=[bad],
                level="ERROR",
                message="fanout-async",
            )
        )

    assert (
        "Async component dispatch failed for component type=AsyncComponent"
        in caplog.text
    )
