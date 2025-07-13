#!/usr/bin/env python3
"""
Test script to verify core async components work correctly (for async_hydra).
"""

import asyncio
import time
import pytest
from hydra_logger.async_hydra.core import (
    CoroutineManager,
    EventLoopManager,
    BoundedAsyncQueue,
    MemoryMonitor,
    SafeShutdownManager,
    AsyncErrorTracker,
    AsyncHealthMonitor
)


@pytest.mark.asyncio
async def test_coroutine_manager():
    print("Testing CoroutineManager...")
    manager = CoroutineManager()
    async def test_task():
        await asyncio.sleep(0.1)
        return "task completed"
    task = manager.track(test_task())
    result = await task
    assert result == "task completed"
    await manager.shutdown()
    stats = manager.get_stats()
    assert stats['stats']['tasks_created'] == 1
    assert stats['stats']['tasks_completed'] == 1
    print("✓ CoroutineManager test passed")


@pytest.mark.asyncio
async def test_event_loop_manager():
    print("Testing EventLoopManager...")
    assert EventLoopManager.has_running_loop() == True
    async def test_task():
        return "test"
    task = EventLoopManager.safe_create_task(test_task())
    result = await task
    assert result == "test"
    async def async_op():
        return "async result"
    def sync_op():
        return "sync result"
    result = await EventLoopManager.safe_async_operation(async_op, sync_op)
    assert result == "async result"
    print("✓ EventLoopManager test passed")


@pytest.mark.asyncio
async def test_bounded_queue():
    print("Testing BoundedAsyncQueue...")
    queue = BoundedAsyncQueue(maxsize=3)
    await queue.put("test1")
    await queue.put("test2")
    item1 = await queue.get()
    item2 = await queue.get()
    assert item1 == "test1"
    assert item2 == "test2"
    assert queue.qsize() == 0
    assert queue.empty() == True
    stats = queue.get_stats()
    assert stats['stats']['puts'] == 2
    assert stats['stats']['gets'] == 2
    print("✓ BoundedAsyncQueue test passed")


def test_memory_monitor():
    print("Testing MemoryMonitor...")
    monitor = MemoryMonitor(max_percent=90.0)
    is_healthy = monitor.check_memory()
    assert isinstance(is_healthy, bool)
    stats = monitor.get_memory_stats()
    assert 'current_percent' in stats or 'psutil_available' in stats
    print("✓ MemoryMonitor test passed")


@pytest.mark.asyncio
async def test_error_tracker():
    print("Testing AsyncErrorTracker...")
    tracker = AsyncErrorTracker()
    await tracker.record_error("test_error", Exception("test exception"))
    stats = tracker.get_error_stats()
    assert stats['total_errors'] == 1
    assert stats['error_counts']['test_error'] == 1
    tracker.record_error_sync("sync_error", Exception("sync exception"))
    stats = tracker.get_error_stats()
    assert stats['total_errors'] == 2
    print("✓ AsyncErrorTracker test passed")


@pytest.mark.asyncio
async def test_health_monitor():
    print("Testing AsyncHealthMonitor...")
    monitor = AsyncHealthMonitor()
    status = monitor.get_health_status()
    assert 'uptime' in status
    assert 'is_healthy' in status
    metrics = monitor.get_performance_metrics()
    assert 'uptime' in metrics
    print("✓ AsyncHealthMonitor test passed")


@pytest.mark.asyncio
async def test_shutdown_manager():
    print("Testing SafeShutdownManager...")
    manager = SafeShutdownManager(flush_timeout=1.0, cleanup_timeout=1.0)
    await manager.shutdown()
    stats = manager.get_stats()
    assert stats['phase'] == 'done'
    assert stats['shutdown_requested'] == True
    print("✓ SafeShutdownManager test passed")


async def main():
    print("Running core async component tests...\n")
    try:
        await test_coroutine_manager()
        await test_event_loop_manager()
        await test_bounded_queue()
        test_memory_monitor()
        await test_error_tracker()
        await test_health_monitor()
        await test_shutdown_manager()
        print("\n🎉 All core component tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 