"""
Tests for async queue functionality.

This module tests the async queue system including AsyncLogQueue,
AsyncBatchProcessor, and AsyncBackpressureHandler.
"""

import asyncio
import logging
import pytest
import time
from unittest.mock import Mock, patch

from hydra_logger.async_hydra.async_queue import (
    AsyncLogQueue, AsyncBatchProcessor, AsyncBackpressureHandler, QueueStats
)


class TestAsyncLogQueue:
    """Test AsyncLogQueue functionality."""
    
    @pytest.mark.asyncio
    async def test_async_log_queue_initialization(self):
        """Test AsyncLogQueue initialization."""
        queue = AsyncLogQueue(max_size=100, batch_size=10, batch_timeout=0.5)
        
        assert queue.max_size == 100
        assert queue.batch_size == 10
        assert queue.batch_timeout == 0.5
        assert queue.processor is None
        assert not queue._running
    
    @pytest.mark.asyncio
    async def test_async_log_queue_put_get(self):
        """Test putting and getting messages from queue."""
        queue = AsyncLogQueue(max_size=10)
        await queue.start()
        
        # Put message
        success = await queue.put("test message")
        assert success is True
        
        # Get message
        message = await queue.get()
        assert message == "test message"
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_full(self):
        """Test queue behavior when full."""
        queue = AsyncLogQueue(max_size=1, batch_size=1, batch_timeout=0.01)
        
        try:
            await queue.start()
            
            # Fill queue
            success1 = await queue.put("message 1")
            assert success1 is True
            
            # Try to put another message immediately (should fail because queue is full)
            success2 = await queue.put("message 2")
            assert success2 is False
            
            # Wait a bit for processing
            await asyncio.sleep(0.1)
            
            # Now try to put another message (should succeed because first was processed)
            success3 = await queue.put("message 3")
            assert success3 is True
            
            # Check stats
            stats = queue.get_stats()
            assert stats.dropped_messages == 1
            
        finally:
            # Ensure cleanup happens
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_with_processor(self):
        """Test queue with custom processor."""
        processed_messages = []
        
        async def custom_processor(messages):
            processed_messages.extend(messages)
        
        queue = AsyncLogQueue(max_size=10, batch_size=2, batch_timeout=0.05, processor=custom_processor)
        await queue.start()
        
        # Put messages
        await queue.put("message 1")
        await queue.put("message 2")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        assert len(processed_messages) >= 2
        assert "message 1" in processed_messages
        assert "message 2" in processed_messages
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_batch_processing(self):
        """Test batch processing functionality."""
        processed_batches = []
        
        async def batch_processor(messages):
            processed_batches.append(messages)
        
        queue = AsyncLogQueue(max_size=10, batch_size=3, processor=batch_processor)
        await queue.start()
        
        # Put messages to trigger batch processing
        for i in range(5):
            await queue.put(f"message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        assert len(processed_batches) > 0
        assert any(len(batch) >= 3 for batch in processed_batches)
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_timeout_processing(self):
        """Test timeout-based batch processing."""
        processed_batches = []
        
        async def batch_processor(messages):
            processed_batches.append(messages)
        
        queue = AsyncLogQueue(max_size=10, batch_size=100, batch_timeout=0.1, processor=batch_processor)
        await queue.start()
        
        # Put one message
        await queue.put("timeout test message")
        
        # Wait for timeout
        await asyncio.sleep(0.2)
        
        assert len(processed_batches) > 0
        assert "timeout test message" in processed_batches[0]
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_error_handling(self):
        """Test error handling in queue worker."""
        error_count = 0
        
        async def error_processor(messages):
            nonlocal error_count
            error_count += 1
            raise Exception("Test error")
        
        queue = AsyncLogQueue(max_size=10, processor=error_processor)
        await queue.start()
        
        # Put message that will cause error
        await queue.put("error test")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Should not crash, error should be handled
        assert error_count > 0
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_stats(self):
        """Test queue statistics."""
        queue = AsyncLogQueue(max_size=10)
        await queue.start()
        
        # Put some messages
        for i in range(5):
            await queue.put(f"message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        stats = queue.get_stats()
        assert stats.total_messages >= 5
        assert stats.processed_messages >= 5
        assert stats.queue_size == 0  # All processed
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_reset_stats(self):
        """Test resetting queue statistics."""
        queue = AsyncLogQueue(max_size=10)
        await queue.start()
        
        # Put some messages
        await queue.put("test message")
        await asyncio.sleep(0.1)
        
        # Check stats
        stats_before = queue.get_stats()
        assert stats_before.total_messages > 0
        
        # Reset stats
        queue.reset_stats()
        
        # Check stats after reset
        stats_after = queue.get_stats()
        assert stats_after.total_messages == 0
        assert stats_after.processed_messages == 0
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_double_start_stop(self):
        """Test double start and stop operations."""
        queue = AsyncLogQueue(max_size=10)
        
        # Double start
        await queue.start()
        await queue.start()  # Should be no-op
        
        assert queue._running is True
        
        # Double stop
        await queue.stop()
        await queue.stop()  # Should be no-op
        
        assert queue._running is False
    
    @pytest.mark.asyncio
    async def test_async_log_queue_get_timeout(self):
        """Test queue get with timeout."""
        queue = AsyncLogQueue(max_size=10)
        await queue.start()
        
        # Try to get with timeout (should timeout)
        with pytest.raises(asyncio.TimeoutError):
            await queue.get()
        
        await queue.stop()


class TestAsyncBatchProcessor:
    """Test AsyncBatchProcessor functionality."""
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_initialization(self):
        """Test AsyncBatchProcessor initialization."""
        processor = AsyncBatchProcessor(batch_size=50, batch_timeout=0.5)
        
        assert processor.batch_size == 50
        assert processor.batch_timeout == 0.5
        assert processor.processor is None
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_add_message(self):
        """Test adding messages to batch processor."""
        processed_messages = []
        
        async def custom_processor(messages):
            processed_messages.extend(messages)
        
        processor = AsyncBatchProcessor(batch_size=3, processor=custom_processor)
        await processor.start()
        
        try:
            # Add messages
            for i in range(5):
                await processor.add_message(f"message {i}")
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            assert len(processed_messages) >= 3  # At least one batch should be processed
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_timeout(self):
        """Test batch processor timeout behavior."""
        processed_messages = []
        
        async def custom_processor(messages):
            processed_messages.extend(messages)
        
        processor = AsyncBatchProcessor(batch_size=100, batch_timeout=0.1, processor=custom_processor)
        await processor.start()
        
        try:
            # Add one message
            await processor.add_message("timeout test")
            
            # Wait for timeout - now it should auto-process
            await asyncio.sleep(0.2)
            
            # Message should be processed automatically
            assert len(processed_messages) > 0
            assert "timeout test" in processed_messages
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_manual_process(self):
        """Test manual batch processing."""
        processed_messages = []
        
        async def custom_processor(messages):
            processed_messages.extend(messages)
        
        processor = AsyncBatchProcessor(batch_size=10, processor=custom_processor)
        await processor.start()
        
        try:
            # Add messages
            await processor.add_message("message 1")
            await processor.add_message("message 2")
            
            # Manually process batch
            await processor.process_batch()
            
            assert len(processed_messages) == 2
            assert "message 1" in processed_messages
            assert "message 2" in processed_messages
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_error_handling(self):
        """Test error handling in batch processor."""
        error_count = 0
        
        async def error_processor(messages):
            nonlocal error_count
            error_count += 1
            raise Exception("Test error")
        
        processor = AsyncBatchProcessor(batch_size=2, processor=error_processor)
        await processor.start()
        
        try:
            # Add messages to trigger error
            await processor.add_message("error test 1")
            await processor.add_message("error test 2")
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Should not crash, error should be handled
            assert error_count > 0
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_stats(self):
        """Test batch processor statistics."""
        processor = AsyncBatchProcessor(batch_size=2)
        await processor.start()
        
        try:
            # Add messages
            for i in range(5):
                await processor.add_message(f"message {i}")
            
            # Wait for processing - wait a bit longer to ensure all messages are processed
            await asyncio.sleep(0.2)
            
            stats = processor.get_stats()
            assert stats.total_messages >= 5
            assert stats.processed_messages >= 4  # Allow for timing variations
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_reset_stats(self):
        """Test resetting batch processor statistics."""
        processor = AsyncBatchProcessor(batch_size=2)
        await processor.start()
        
        try:
            # Add messages
            await processor.add_message("test message")
            await asyncio.sleep(0.1)
            
            # Check stats
            stats_before = processor.get_stats()
            assert stats_before.total_messages > 0
            
            # Reset stats
            processor.reset_stats()
            
            # Check stats after reset
            stats_after = processor.get_stats()
            assert stats_after.total_messages == 0
            assert stats_after.processed_messages == 0
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_start_stop(self):
        """Test batch processor start and stop operations."""
        processed_messages = []
        
        async def custom_processor(messages):
            processed_messages.extend(messages)
        
        processor = AsyncBatchProcessor(batch_size=2, batch_timeout=0.1, processor=custom_processor)
        
        # Start processor
        await processor.start()
        assert processor._running is True
        
        # Add messages
        await processor.add_message("message 1")
        await processor.add_message("message 2")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Stop processor
        await processor.stop()
        assert processor._running is False
        
        # Check that messages were processed
        assert len(processed_messages) >= 2


class TestAsyncBackpressureHandler:
    """Test AsyncBackpressureHandler functionality."""
    
    @pytest.mark.asyncio
    async def test_async_backpressure_handler_initialization(self):
        """Test AsyncBackpressureHandler initialization."""
        handler = AsyncBackpressureHandler(
            max_queue_size=1000,
            drop_threshold=0.9,
            slow_down_threshold=0.7
        )
        
        assert handler.max_queue_size == 1000
        assert handler.drop_threshold == 0.9
        assert handler.slow_down_threshold == 0.7
    
    @pytest.mark.asyncio
    async def test_async_backpressure_handler_should_accept_message(self):
        """Test message acceptance logic."""
        handler = AsyncBackpressureHandler(max_queue_size=100, drop_threshold=0.9)
        
        # Test normal queue size
        should_accept = await handler.should_accept_message(50)
        assert should_accept is True
        
        # Test at drop threshold
        should_accept = await handler.should_accept_message(90)
        assert should_accept is False
    
    @pytest.mark.asyncio
    async def test_async_backpressure_handler_processing_delay(self):
        """Test processing delay calculation."""
        handler = AsyncBackpressureHandler(
            max_queue_size=100,
            slow_down_threshold=0.7
        )
        
        # Test normal queue size
        delay = await handler.get_processing_delay(50)
        assert delay == 0.0
        
        # Test at slow down threshold
        delay = await handler.get_processing_delay(70)
        assert delay > 0.0
        
        # Test high queue size
        delay = await handler.get_processing_delay(90)
        assert delay > 0.0
    
    @pytest.mark.asyncio
    async def test_async_backpressure_handler_update_queue_size(self):
        """Test queue size updates."""
        handler = AsyncBackpressureHandler(max_queue_size=100)
        
        # Update queue size
        await handler.update_queue_size(50)
        
        # Test acceptance
        should_accept = await handler.should_accept_message(50)
        assert should_accept is True
    
    @pytest.mark.asyncio
    async def test_async_backpressure_handler_stats(self):
        """Test backpressure handler statistics."""
        handler = AsyncBackpressureHandler(max_queue_size=100)
        
        # Update queue size
        await handler.update_queue_size(50)
        
        stats = handler.get_stats()
        assert stats.queue_size == 50
    
    @pytest.mark.asyncio
    async def test_async_backpressure_handler_reset_stats(self):
        """Test resetting backpressure handler statistics."""
        handler = AsyncBackpressureHandler(max_queue_size=100)
        
        # Update queue size
        await handler.update_queue_size(50)
        
        # Check stats
        stats_before = handler.get_stats()
        assert stats_before.queue_size == 50
        
        # Reset stats
        handler.reset_stats()
        
        # Check stats after reset
        stats_after = handler.get_stats()
        assert stats_after.queue_size == 0


class TestQueueStats:
    """Test QueueStats dataclass."""
    
    def test_queue_stats_initialization(self):
        """Test QueueStats initialization."""
        stats = QueueStats()
        
        assert stats.total_messages == 0
        assert stats.processed_messages == 0
        assert stats.dropped_messages == 0
        assert stats.queue_size == 0
        assert stats.max_queue_size == 0
        assert stats.avg_processing_time == 0.0
        assert stats.total_processing_time == 0.0
        assert stats.batch_count == 0
        assert stats.last_batch_time == 0.0
    
    def test_queue_stats_with_values(self):
        """Test QueueStats with custom values."""
        stats = QueueStats(
            total_messages=100,
            processed_messages=95,
            dropped_messages=5,
            queue_size=10,
            max_queue_size=50,
            avg_processing_time=0.1,
            total_processing_time=10.0,
            batch_count=20,
            last_batch_time=time.time()
        )
        
        assert stats.total_messages == 100
        assert stats.processed_messages == 95
        assert stats.dropped_messages == 5
        assert stats.queue_size == 10
        assert stats.max_queue_size == 50
        assert stats.avg_processing_time == 0.1
        assert stats.total_processing_time == 10.0
        assert stats.batch_count == 20
        assert stats.last_batch_time > 0


class TestAsyncQueueIntegration:
    """Integration tests for async queue components."""
    
    @pytest.mark.asyncio
    async def test_queue_with_backpressure(self):
        """Test queue with backpressure handler."""
        queue = AsyncLogQueue(max_size=10)
        backpressure = AsyncBackpressureHandler(max_queue_size=10)
        
        await queue.start()
        
        # Test normal operation
        should_accept = await backpressure.should_accept_message(5)
        assert should_accept is True
        
        # Put messages
        for i in range(5):
            success = await queue.put(f"message {i}")
            assert success is True
        
        # Update backpressure
        await backpressure.update_queue_size(5)
        
        # Test backpressure
        should_accept = await backpressure.should_accept_message(5)
        assert should_accept is True
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_batch_processor_with_queue(self):
        """Test batch processor with queue integration."""
        processed_messages = []
        
        async def processor(messages):
            processed_messages.extend(messages)
        
        batch_processor = AsyncBatchProcessor(batch_size=3, processor=processor)
        queue = AsyncLogQueue(max_size=10, processor=batch_processor.processor)
        
        await queue.start()
        
        # Add messages through batch processor
        for i in range(5):
            await batch_processor.add_message(f"message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        assert len(processed_messages) >= 3
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_queue_performance_under_load(self):
        """Test queue performance under load."""
        processed_count = 0
        
        async def fast_processor(messages):
            nonlocal processed_count
            processed_count += len(messages)
        
        queue = AsyncLogQueue(max_size=100, batch_size=10, processor=fast_processor)
        await queue.start()
        
        # Send many messages quickly
        start_time = time.time()
        for i in range(50):
            await queue.put(f"load test message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process quickly
        assert processing_time < 1.0
        assert processed_count >= 40  # Most messages should be processed
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_queue_error_recovery(self):
        """Test queue error recovery."""
        error_count = 0
        success_count = 0
        
        async def mixed_processor(messages):
            nonlocal error_count, success_count
            for msg in messages:
                if "error" in str(msg):
                    error_count += 1
                    raise Exception("Test error")
                else:
                    success_count += 1
        
        queue = AsyncLogQueue(max_size=10, processor=mixed_processor)
        await queue.start()
        
        # Send mixed messages
        for i in range(10):
            if i % 2 == 0:
                await queue.put(f"error message {i}")
            else:
                await queue.put(f"success message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Should handle both errors and successes
        assert error_count > 0
        assert success_count > 0
        
        await queue.stop()


class TestDataLossProtection:
    """Test data loss protection functionality."""
    
    @pytest.mark.asyncio
    async def test_data_loss_protection_backup_restore(self):
        """Test backup and restore functionality."""
        from hydra_logger.async_hydra.async_queue import DataLossProtection
        
        protection = DataLossProtection(backup_dir=".test_backup")
        
        # Create a test message
        test_message = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Backup message
        success = await protection.backup_message(test_message, "test_queue")
        assert success is True
        
        # Restore messages
        restored = await protection.restore_messages("test_queue")
        assert len(restored) == 1
        assert isinstance(restored[0], logging.LogRecord)
        assert restored[0].getMessage() == "Test message"
        
        # Cleanup
        import shutil
        shutil.rmtree(".test_backup", ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_queue_with_data_protection(self):
        """Test queue with data loss protection enabled."""
        processed_messages = []
        
        async def slow_processor(messages):
            # Simulate slow processing to trigger backup
            await asyncio.sleep(0.1)
            processed_messages.extend(messages)
        
        # Create queue with data protection and small batch size
        queue = AsyncLogQueue(
            max_size=1,  # Very small queue to trigger backup
            batch_size=1,
            processor=slow_processor,
            enable_data_protection=True
        )
        
        await queue.start()
        
        try:
            # Fill queue beyond capacity - first message goes in queue
            success1 = await queue.put("message 1")
            assert success1 is True
            
            # Second message should be backed up
            success2 = await queue.put("message 2")
            assert success2 is True  # Should be backed up
            
            # Third message should also be backed up
            success3 = await queue.put("message 3")
            assert success3 is True  # Should be backed up
            
            # Wait for processing
            await asyncio.sleep(0.3)
            
            # Check stats
            stats = queue.get_stats()
            assert stats.total_messages >= 3
            assert stats.failed_messages >= 2  # At least 2 messages backed up
            
            # Check protection stats
            protection_stats = queue.get_data_protection_stats()
            assert protection_stats is not None
            assert protection_stats["backup_files"] >= 2
            
        finally:
            await queue.stop()
            
            # Cleanup
            import shutil
            shutil.rmtree(".hydra_backup", ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_queue_without_data_protection(self):
        """Test queue without data loss protection."""
        processed_messages = []
        
        async def processor(messages):
            processed_messages.extend(messages)
        
        # Create queue without data protection
        queue = AsyncLogQueue(
            max_size=2,
            batch_size=1,
            processor=processor,
            enable_data_protection=False
        )
        
        await queue.start()
        
        try:
            # Fill queue beyond capacity
            for i in range(5):
                success = await queue.put(f"message {i}")
                if i < 2:
                    assert success is True
                else:
                    assert success is False  # Messages dropped
            
            # Wait for processing
            await asyncio.sleep(0.2)
            
            # Check stats
            stats = queue.get_stats()
            assert stats.dropped_messages > 0
            
            # Check protection stats
            protection_stats = queue.get_data_protection_stats()
            assert protection_stats is None
            
        finally:
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self):
        """Test circuit breaker pattern in data protection."""
        from hydra_logger.async_hydra.async_queue import DataLossProtection
        
        protection = DataLossProtection()
        
        # Simulate failures
        for i in range(3):
            should_retry = await protection.should_retry(Exception("Test error"))
            assert should_retry is True
        
        # After 5 failures, circuit should open
        for i in range(5):
            should_retry = await protection.should_retry(Exception("Test error"))
            if i < 4:
                assert should_retry is True
            else:
                assert should_retry is False  # Circuit open
        
        # Check stats
        stats = protection.get_protection_stats()
        assert stats["circuit_open"] is True
        assert stats["failure_count"] >= 5


class TestAsyncQueueEdgeCases:
    """Test edge cases and error conditions for 100% coverage."""
    
    @pytest.mark.asyncio
    async def test_queue_put_exception_handling(self):
        """Test exception handling in put method."""
        queue = AsyncLogQueue(max_size=1)
        
        # Mock queue.put to raise exception
        with patch.object(queue._queue, 'put', side_effect=Exception("Queue error")):
            success = await queue.put("test message")
            assert success is False
    
    @pytest.mark.asyncio
    async def test_queue_get_timeout(self):
        """Test queue get with timeout."""
        queue = AsyncLogQueue(max_size=10)
        await queue.start()
        
        try:
            # Try to get with timeout
            with pytest.raises(asyncio.TimeoutError):
                await queue.get()
        finally:
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_queue_double_start_stop(self):
        """Test double start and stop operations."""
        queue = AsyncLogQueue(max_size=10)
        
        # Double start
        await queue.start()
        await queue.start()  # Should be no-op
        assert queue._running is True
        
        # Double stop
        await queue.stop()
        await queue.stop()  # Should be no-op
        assert queue._running is False
    
    @pytest.mark.asyncio
    async def test_worker_cancellation(self):
        """Test worker task cancellation."""
        queue = AsyncLogQueue(max_size=10)
        await queue.start()
        
        # Cancel worker task
        if queue._worker_task:
            queue._worker_task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await queue._worker_task
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_worker_exception_handling(self):
        """Test worker exception handling."""
        processed_messages = []
        
        async def error_processor(messages):
            processed_messages.extend(messages)
            raise Exception("Processor error")
        
        queue = AsyncLogQueue(max_size=10, processor=error_processor)
        await queue.start()
        
        try:
            # Add message that will cause error
            await queue.put("error test")
            await asyncio.sleep(0.1)
            
            # Should not crash
            assert queue._running is True
        finally:
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_batch_processor_worker_exception(self):
        """Test batch processor worker exception handling."""
        processor = AsyncBatchProcessor(batch_size=2)
        await processor.start()
        
        try:
            # Add messages
            await processor.add_message("test 1")
            await processor.add_message("test 2")
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Should not crash
            assert processor._running is True
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_data_protection_backup_failure(self):
        """Test data protection backup failure handling."""
        from hydra_logger.async_hydra.async_queue import DataLossProtection
        
        # Mock backup to fail
        protection = DataLossProtection(backup_dir="/invalid/path")
        
        test_message = "test message"
        success = await protection.backup_message(test_message, "test")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_data_protection_restore_failure(self):
        """Test data protection restore failure handling."""
        from hydra_logger.async_hydra.async_queue import DataLossProtection
        
        protection = DataLossProtection(backup_dir=".test_backup")
        
        # Create invalid backup file
        backup_file = protection.backup_dir / "test_invalid.json"
        backup_file.parent.mkdir(exist_ok=True)
        with open(backup_file, 'w') as f:
            f.write("invalid json")
        
        # Should handle invalid JSON gracefully
        restored = await protection.restore_messages("test")
        assert len(restored) == 0
        
        # Cleanup
        import shutil
        shutil.rmtree(".test_backup", ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout(self):
        """Test circuit breaker timeout functionality."""
        from hydra_logger.async_hydra.async_queue import DataLossProtection
        
        protection = DataLossProtection()
        
        # Open circuit
        for i in range(5):
            await protection.should_retry(Exception("error"))
        
        # Circuit should be open
        stats = protection.get_protection_stats()
        assert stats["circuit_open"] is True
        
        # Wait for timeout (mock time)
        with patch('time.time', return_value=time.time() + 31):
            should_retry = await protection.should_retry(Exception("error"))
            assert should_retry is True  # Circuit should be closed
    
    @pytest.mark.asyncio
    async def test_queue_with_sync_processor(self):
        """Test queue with synchronous processor."""
        processed_messages = []
        
        def sync_processor(messages):
            processed_messages.extend(messages)
        
        queue = AsyncLogQueue(max_size=10, processor=sync_processor)
        await queue.start()
        
        try:
            await queue.put("test message")
            await asyncio.sleep(0.1)
            
            assert len(processed_messages) > 0
        finally:
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_batch_processor_with_sync_processor(self):
        """Test batch processor with synchronous processor."""
        processed_messages = []
        
        def sync_processor(messages):
            processed_messages.extend(messages)
        
        processor = AsyncBatchProcessor(batch_size=2, processor=sync_processor)
        await processor.start()
        
        try:
            await processor.add_message("test 1")
            await processor.add_message("test 2")
            await asyncio.sleep(0.1)
            
            assert len(processed_messages) >= 2
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_queue_stats_thread_safety(self):
        """Test queue statistics thread safety."""
        queue = AsyncLogQueue(max_size=100)
        await queue.start()
        
        try:
            # Add messages from multiple coroutines
            async def add_messages():
                for i in range(10):
                    await queue.put(f"message {i}")
                    await asyncio.sleep(0.01)
            
            # Run multiple coroutines
            tasks = [add_messages() for _ in range(3)]
            await asyncio.gather(*tasks)
            
            # Check stats
            stats = queue.get_stats()
            assert stats.total_messages >= 30
            
        finally:
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_backpressure_handler_edge_cases(self):
        """Test backpressure handler edge cases."""
        handler = AsyncBackpressureHandler(max_queue_size=0)  # Zero size
        
        # Test with zero queue size
        should_accept = await handler.should_accept_message(0)
        assert should_accept is False
        
        # Test processing delay with zero size
        delay = await handler.get_processing_delay(0)
        assert delay == 0.0
    
    @pytest.mark.asyncio
    async def test_queue_remaining_messages_processing(self):
        """Test processing of remaining messages on stop."""
        processed_messages = []
        
        async def processor(messages):
            processed_messages.extend(messages)
        
        queue = AsyncLogQueue(max_size=10, processor=processor)
        await queue.start()
        
        # Add messages
        for i in range(5):
            await queue.put(f"message {i}")
        
        # Stop immediately - should process remaining messages
        await queue.stop()
        
        # All messages should be processed
        assert len(processed_messages) >= 5
    
    @pytest.mark.asyncio
    async def test_batch_processor_remaining_messages(self):
        """Test batch processor remaining messages on stop."""
        processed_messages = []
        
        async def processor(messages):
            processed_messages.extend(messages)
        
        batch_processor = AsyncBatchProcessor(batch_size=10, processor=processor)
        await batch_processor.start()
        
        # Add messages
        for i in range(5):
            await batch_processor.add_message(f"message {i}")
        
        # Stop immediately - should process remaining messages
        await batch_processor.stop()
        
        # All messages should be processed
        assert len(processed_messages) >= 5
    
    @pytest.mark.asyncio
    async def test_queue_error_recovery_with_retry(self):
        """Test queue error recovery with retry mechanism."""
        error_count = 0
        
        async def failing_processor(messages):
            nonlocal error_count
            error_count += 1
            if error_count < 3:
                raise Exception("Temporary error")
            # Succeed on third attempt
        
        queue = AsyncLogQueue(
            max_size=10, 
            processor=failing_processor,
            enable_data_protection=True
        )
        await queue.start()
        
        try:
            await queue.put("test message")
            await asyncio.sleep(0.3)  # Wait for retries
            
            # Should eventually succeed
            stats = queue.get_stats()
            assert stats.retry_count > 0
            
        finally:
            await queue.stop()
            
            # Cleanup
            import shutil
            shutil.rmtree(".hydra_backup", ignore_errors=True) 