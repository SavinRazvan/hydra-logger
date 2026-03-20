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

from hydra_logger.core.exceptions import HydraLoggerError
from hydra_logger.extensions.extension_base import ExtensionBase, SecurityExtension
from hydra_logger.extensions.extension_manager import ExtensionManager
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


class FailingOwner:
    def __init__(self, raise_hydra_error: bool = False) -> None:
        self.raise_hydra_error = raise_hydra_error
        self.calls = []

    def _handle_internal_failure(self, context: str, error: Exception) -> None:
        self.calls.append((context, str(error)))
        if self.raise_hydra_error:
            raise HydraLoggerError("strict failure")


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


def test_extension_processor_owner_handles_data_protection_failure_context() -> None:
    owner = FailingOwner()
    processor = ExtensionProcessor(owner)
    record = SimpleNamespace(message="secret")
    protection = DummyDataProtection(enabled=True, should_fail=True)

    updated = processor.apply_data_protection(record, protection)
    assert updated.message == "secret"
    assert owner.calls == [("extension_data_protection", "process failed")]


def test_extension_processor_reraises_hydra_error_from_owner() -> None:
    owner = FailingOwner(raise_hydra_error=True)
    processor = ExtensionProcessor(owner)
    record = SimpleNamespace(message="secret")
    protection = DummyDataProtection(enabled=True, should_fail=True)

    with pytest.raises(HydraLoggerError, match="strict failure"):
        processor.apply_data_protection(record, protection)


def test_extension_processor_applies_non_data_extensions_in_order() -> None:
    class SuffixExtension(ExtensionBase):
        def process(self, data):  # type: ignore[no-untyped-def]
            if isinstance(data, str):
                return f"{data}{self.get_config().get('suffix', '')}"
            return data

    manager = ExtensionManager()
    manager.register_extension_type("suffix", SuffixExtension)
    manager.create_extension("append_a", "suffix", enabled=True, suffix=":A")
    manager.create_extension("append_b", "suffix", enabled=True, suffix=":B")
    manager.add_extension(
        "data_protection",
        SecurityExtension(enabled=True, patterns=["token"]),
    )
    manager.set_processing_order(["append_a", "data_protection", "append_b"])

    processor = ExtensionProcessor()
    record = SimpleNamespace(
        message='token="abc"',
        context={"message": 'token="abc"'},
        extra={"note": "x"},
    )
    updated = processor.apply_non_data_protection_extensions(
        record,
        manager,
        manager.get_extension("data_protection"),
    )
    assert updated.message == 'token="abc":A:B'
    assert updated.context["message"] == 'token="abc"'


def test_extension_processor_non_data_extension_failure_uses_owner_policy() -> None:
    class FailingExtension(ExtensionBase):
        def process(self, _data):  # type: ignore[no-untyped-def]
            raise RuntimeError("ext-fail")

    owner = FailingOwner(raise_hydra_error=True)
    manager = ExtensionManager()
    manager.register_extension_type("failing", FailingExtension)
    manager.create_extension("boom", "failing", enabled=True)
    processor = ExtensionProcessor(owner)
    record = SimpleNamespace(message="x", context=None, extra=None)

    with pytest.raises(HydraLoggerError, match="strict failure"):
        processor.apply_non_data_protection_extensions(record, manager, None)


def test_extension_processor_non_data_extensions_returns_record_when_manager_missing() -> (
    None
):
    processor = ExtensionProcessor()
    record = SimpleNamespace(message="x", context={"k": "v"}, extra={"n": 1})

    updated = processor.apply_non_data_protection_extensions(record, None, None)

    assert updated is record
    assert updated.message == "x"
    assert updated.context == {"k": "v"}
    assert updated.extra == {"n": 1}


def test_extension_processor_non_data_extensions_skips_other_security_extensions() -> (
    None
):
    class SuffixExtension(ExtensionBase):
        def process(self, data):  # type: ignore[no-untyped-def]
            if isinstance(data, str):
                return f"{data}:N"
            return data

    manager = ExtensionManager()
    manager.register_extension_type("suffix", SuffixExtension)
    manager.create_extension("append_non_security", "suffix", enabled=True)
    manager.add_extension(
        "security_other", SecurityExtension(enabled=True, patterns=["x"])
    )
    manager.set_processing_order(["security_other", "append_non_security"])

    processor = ExtensionProcessor()
    record = SimpleNamespace(message="msg", context=None, extra=None)

    updated = processor.apply_non_data_protection_extensions(
        record,
        manager,
        None,
    )

    assert updated.message == "msg:N"


def test_extension_processor_non_data_extensions_skip_disabled_and_log_ownerless_failures(
    caplog,
) -> None:
    class DisabledExtension(ExtensionBase):
        def process(self, data):  # type: ignore[no-untyped-def]
            return f"disabled:{data}"

    class FailingExtension(ExtensionBase):
        def process(self, _data):  # type: ignore[no-untyped-def]
            raise RuntimeError("no-owner-fail")

    manager = ExtensionManager()
    manager.register_extension_type("disabled_ext", DisabledExtension)
    manager.register_extension_type("failing_ext", FailingExtension)
    manager.create_extension("disabled_one", "disabled_ext", enabled=False)
    manager.create_extension("failing_one", "failing_ext", enabled=True)
    manager.set_processing_order(["disabled_one", "failing_one"])

    processor = ExtensionProcessor()
    record = SimpleNamespace(message="x", context=None, extra=None)
    with caplog.at_level(
        "ERROR", logger="hydra_logger.loggers.pipeline.extension_processor"
    ):
        updated = processor.apply_non_data_protection_extensions(record, manager, None)
    assert updated.message == "x"
    assert "Extension processing failed for extension=failing_one" in caplog.text


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
