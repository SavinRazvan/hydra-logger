"""
Comprehensive tests for BoundedAsyncQueue to cover missing lines.

This module targets specific uncovered lines in bounded_queue.py to achieve
higher coverage through edge cases, error conditions, and policy testing.
"""

import asyncio
import pytest
import time
from unittest.mock import patch, MagicMock

from hydra_logger.async_hydra.core.bounded_queue import BoundedAsyncQueue, QueuePolicy


class TestBoundedAsyncQueueCoverage:
    """Comprehensive tests for BoundedAsyncQueue coverage gaps."""

    @pytest.mark.asyncio
    async def test_put_timeout_drop_oldest_policy(self):
        """Test put timeout with DROP_OLDEST policy (lines 78-83)."""
        queue = BoundedAsyncQueue(maxsize=1, policy=QueuePolicy.DROP_OLDEST, put_timeout=0.01)
        
        # Fill the queue
        await queue.put("item1")
        
        # Try to put another item - should timeout and drop oldest
        await queue.put("item2")
        
        # Check that item2 is in queue and item1 was dropped
        item = await queue.get()
        assert item == "item2"
        
        stats = queue.get_stats()
        assert stats['stats']['timeouts'] >= 1
        assert stats['stats']['drops'] >= 1

    @pytest.mark.asyncio
    async def test_put_timeout_drop_oldest_failure(self):
        """Test put timeout with DROP_OLDEST policy when drop fails (lines 87-100)."""
        queue = BoundedAsyncQueue(maxsize=1, policy=QueuePolicy.DROP_OLDEST, put_timeout=0.01)
        
        # Fill the queue
        await queue.put("item1")
        
        # Mock queue to fail get_nowait and put_nowait
        with patch.object(queue._queue, 'get_nowait', side_effect=asyncio.QueueEmpty):
            with pytest.raises(asyncio.QueueFull, match="Queue is full and drop_oldest failed"):
                await queue.put("item2")
        
        stats = queue.get_stats()
        assert stats['stats']['errors'] >= 1

    @pytest.mark.asyncio
    async def test_put_timeout_error_policy(self):
        """Test put timeout with ERROR policy (lines 101-103)."""
        queue = BoundedAsyncQueue(maxsize=1, policy=QueuePolicy.ERROR, put_timeout=0.01)
        
        # Fill the queue
        await queue.put("item1")
        
        # Try to put another item - should raise QueueFull
        with pytest.raises(asyncio.QueueFull, match="Queue put timeout"):
            await queue.put("item2")

    @pytest.mark.asyncio
    async def test_put_timeout_block_policy(self):
        """Test put timeout with BLOCK policy (lines 104-117)."""
        queue = BoundedAsyncQueue(maxsize=1, policy=QueuePolicy.BLOCK, put_timeout=0.01)
        
        # Fill the queue
        await queue.put("item1")
        
        # Try to put another item - should create task
        await queue.put("item2")
        
        # Wait a bit for the task to complete
        await asyncio.sleep(0.1)
        
        # Both items should be in queue (BLOCK policy)
        item1 = await queue.get()
        item2 = await queue.get()
        assert item1 == "item1"
        assert item2 == "item2"

    @pytest.mark.asyncio
    async def test_queue_full_drop_oldest_policy(self):
        """Test queue full with DROP_OLDEST policy (lines 119-131)."""
        queue = BoundedAsyncQueue(maxsize=1, policy=QueuePolicy.DROP_OLDEST)
        
        # Fill the queue
        queue.put_nowait("item1")
        
        # Try to put another item - should drop oldest
        await queue.put("item2")
        
        # Check that item2 is in queue and item1 was dropped
        item = queue.get_nowait()
        assert item == "item2"
        
        stats = queue.get_stats()
        assert stats['stats']['drops'] >= 1

    @pytest.mark.asyncio
    async def test_queue_full_drop_oldest_failure(self):
        """Test queue full with DROP_OLDEST policy when drop fails (lines 132-142)."""
        queue = BoundedAsyncQueue(maxsize=1, policy=QueuePolicy.DROP_OLDEST)
        
        # Fill the queue
        await queue.put("item1")
        
        # Mock queue to fail get_nowait and put_nowait
        with patch.object(queue._queue, 'get_nowait', side_effect=asyncio.QueueEmpty):
            with pytest.raises(asyncio.QueueFull, match="Queue is full and drop_oldest failed"):
                await queue.put("item2")
        
        stats = queue.get_stats()
        assert stats['stats']['errors'] >= 1

    @pytest.mark.asyncio
    async def test_queue_full_error_policy(self):
        """Test queue full with ERROR policy (lines 143-145)."""
        queue = BoundedAsyncQueue(maxsize=1, policy=QueuePolicy.ERROR)
        
        # Fill the queue
        await queue.put("item1")
        
        # Try to put another item - should raise QueueFull
        with pytest.raises(asyncio.QueueFull, match="Queue put timeout"):
            await queue.put("item2")

    @pytest.mark.asyncio
    async def test_queue_full_block_policy(self):
        """Test queue full with BLOCK policy (lines 146-154)."""
        queue = BoundedAsyncQueue(maxsize=1, policy=QueuePolicy.BLOCK)
        
        # Fill the queue
        await queue.put("item1")
        
        # Try to put another item - should block until space available
        # Create a task to get an item after a short delay
        async def get_item():
            await asyncio.sleep(0.1)
            return queue.get_nowait()
        
        # Start the get task
        get_task = asyncio.create_task(get_item())
        
        # Put another item - should block until get completes
        await queue.put("item2")
        
        # Wait for get task to complete
        item1 = await get_task
        
        # Check that both items were processed correctly
        assert item1 == "item1"
        item2 = queue.get_nowait()
        assert item2 == "item2"

    @pytest.mark.asyncio
    async def test_get_timeout(self):
        """Test get with timeout (lines 156-162)."""
        queue = BoundedAsyncQueue(get_timeout=0.01)
        
        # Try to get from empty queue - should timeout
        result = await queue.get()
        assert result is None
        
        stats = queue.get_stats()
        assert stats['stats']['timeouts'] >= 1

    @pytest.mark.asyncio
    async def test_get_nowait_empty_queue(self):
        """Test get_nowait with empty queue (lines 164-172)."""
        queue = BoundedAsyncQueue()
        
        # Try to get from empty queue - should raise QueueEmpty
        with pytest.raises(asyncio.QueueEmpty):
            queue.get_nowait()

    @pytest.mark.asyncio
    async def test_put_nowait_full_queue(self):
        """Test put_nowait with full queue (lines 174-182)."""
        queue = BoundedAsyncQueue(maxsize=1)
        
        # Fill the queue
        queue.put_nowait("item1")
        
        # Try to put another item - should raise QueueFull
        with pytest.raises(asyncio.QueueFull):
            queue.put_nowait("item2")

    @pytest.mark.asyncio
    async def test_queue_properties(self):
        """Test queue properties (lines 184-200)."""
        queue = BoundedAsyncQueue(maxsize=5)
        
        # Test empty queue
        assert queue.qsize() == 0
        assert queue.empty() is True
        assert queue.full() is False
        assert queue.maxsize() == 5
        
        # Add items
        await queue.put("item1")
        await queue.put("item2")
        
        # Test non-empty queue
        assert queue.qsize() == 2
        assert queue.empty() is False
        assert queue.full() is False
        
        # Fill queue
        await queue.put("item3")
        await queue.put("item4")
        await queue.put("item5")
        
        # Test full queue
        assert queue.full() is True

    @pytest.mark.asyncio
    async def test_dropped_count(self):
        """Test dropped count tracking (lines 202-204)."""
        queue = BoundedAsyncQueue(maxsize=1, policy=QueuePolicy.DROP_OLDEST)
        
        # Fill queue and add more items to trigger drops
        await queue.put("item1")
        await queue.put("item2")  # Should drop item1
        await queue.put("item3")  # Should drop item2
        
        assert queue.get_dropped_count() >= 2

    @pytest.mark.asyncio
    async def test_comprehensive_stats(self):
        """Test comprehensive statistics (lines 206-220)."""
        queue = BoundedAsyncQueue(maxsize=2, policy=QueuePolicy.DROP_OLDEST)
        
        # Perform various operations
        await queue.put("item1")
        await queue.put("item2")
        await queue.put("item3")  # Should drop item1
        item = await queue.get()
        
        stats = queue.get_stats()
        
        # Check all stats fields
        assert 'size' in stats
        assert 'maxsize' in stats
        assert 'dropped_count' in stats
        assert 'policy' in stats
        assert 'put_timeout' in stats
        assert 'get_timeout' in stats
        assert 'stats' in stats
        assert 'uptime' in stats
        assert 'is_empty' in stats
        assert 'is_full' in stats
        
        # Check nested stats
        assert stats['stats']['puts'] >= 3
        assert stats['stats']['gets'] >= 1
        assert stats['stats']['drops'] >= 1

    @pytest.mark.asyncio
    async def test_reset_stats(self):
        """Test statistics reset (lines 222-232)."""
        queue = BoundedAsyncQueue()
        
        # Perform some operations
        await queue.put("item1")
        await queue.get()
        
        # Get initial stats
        initial_stats = queue.get_stats()
        assert initial_stats['stats']['puts'] >= 1
        assert initial_stats['stats']['gets'] >= 1
        
        # Reset stats
        queue.reset_stats()
        
        # Get reset stats
        reset_stats = queue.get_stats()
        assert reset_stats['stats']['puts'] == 0
        assert reset_stats['stats']['gets'] == 0
        assert reset_stats['stats']['drops'] == 0
        assert reset_stats['stats']['timeouts'] == 0
        assert reset_stats['stats']['errors'] == 0
        assert reset_stats['stats']['queue_full_count'] == 0
        assert reset_stats['dropped_count'] == 0

    @pytest.mark.asyncio
    async def test_set_policy(self):
        """Test policy setting (lines 234-236)."""
        queue = BoundedAsyncQueue(policy=QueuePolicy.DROP_OLDEST)
        assert queue._policy == QueuePolicy.DROP_OLDEST
        
        queue.set_policy(QueuePolicy.ERROR)
        assert queue._policy == QueuePolicy.ERROR
        
        queue.set_policy(QueuePolicy.BLOCK)
        assert queue._policy == QueuePolicy.BLOCK

    @pytest.mark.asyncio
    async def test_set_timeouts(self):
        """Test timeout setting (lines 238-244)."""
        queue = BoundedAsyncQueue(put_timeout=0.1, get_timeout=1.0)
        
        # Test setting put timeout only
        queue.set_timeouts(put_timeout=0.5)
        assert queue._put_timeout == 0.5
        assert queue._get_timeout == 1.0
        
        # Test setting get timeout only
        queue.set_timeouts(get_timeout=2.0)
        assert queue._put_timeout == 0.5
        assert queue._get_timeout == 2.0
        
        # Test setting both
        queue.set_timeouts(put_timeout=0.3, get_timeout=1.5)
        assert queue._put_timeout == 0.3
        assert queue._get_timeout == 1.5

    @pytest.mark.asyncio
    async def test_clear_queue(self):
        """Test queue clearing (lines 246-252)."""
        queue = BoundedAsyncQueue()
        
        # Add items
        await queue.put("item1")
        await queue.put("item2")
        await queue.put("item3")
        
        assert queue.qsize() == 3
        
        # Clear queue
        await queue.clear()
        
        assert queue.qsize() == 0
        assert queue.empty() is True

    @pytest.mark.asyncio
    async def test_clear_empty_queue(self):
        """Test clearing empty queue (lines 246-252)."""
        queue = BoundedAsyncQueue()
        
        # Clear empty queue
        await queue.clear()
        
        assert queue.qsize() == 0
        assert queue.empty() is True

    @pytest.mark.asyncio
    async def test_len_operator(self):
        """Test __len__ operator (lines 254-256)."""
        queue = BoundedAsyncQueue()
        
        assert len(queue) == 0
        
        await queue.put("item1")
        assert len(queue) == 1
        
        await queue.put("item2")
        assert len(queue) == 2

    @pytest.mark.asyncio
    async def test_bool_operator(self):
        """Test __bool__ operator (lines 258-260)."""
        queue = BoundedAsyncQueue()
        
        # Empty queue should be False
        assert bool(queue) is False
        
        # Non-empty queue should be True
        await queue.put("item1")
        assert bool(queue) is True
        
        # Empty queue again should be False
        await queue.get()
        assert bool(queue) is False

    @pytest.mark.asyncio
    async def test_edge_case_operations(self):
        """Test edge cases and error conditions."""
        queue = BoundedAsyncQueue(maxsize=1, policy=QueuePolicy.DROP_OLDEST)
        
        # Test with very short timeouts
        queue.set_timeouts(put_timeout=0.001, get_timeout=0.001)
        
        # Fill queue and trigger timeout
        await queue.put("item1")
        await queue.put("item2")  # Should timeout and drop oldest
        
        # Test get with timeout
        result = await queue.get()
        assert result == "item2"
        
        # Test get from empty queue
        result = await queue.get()
        assert result is None

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent put and get operations."""
        queue = BoundedAsyncQueue(maxsize=10)
        
        # Start multiple producers and consumers
        async def producer(id: int):
            for i in range(5):
                await queue.put(f"item_{id}_{i}")
                await asyncio.sleep(0.01)
        
        async def consumer(id: int):
            for i in range(5):
                item = await queue.get()
                assert item is not None
                await asyncio.sleep(0.01)
        
        # Run concurrent operations
        producers = [producer(i) for i in range(3)]
        consumers = [consumer(i) for i in range(3)]
        
        await asyncio.gather(*producers, *consumers)
        
        # Queue should be empty
        assert queue.empty() is True
        
        # Check stats
        stats = queue.get_stats()
        assert stats['stats']['puts'] >= 15
        assert stats['stats']['gets'] >= 15 