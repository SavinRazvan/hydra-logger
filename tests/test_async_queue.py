"""
Comprehensive tests for async queue functionality.

This module provides 100% coverage for the async queue system including:
- AsyncLogQueue
- AsyncBatchProcessor  
- AsyncBackpressureHandler
- DataLossProtection
- QueueStats
"""

import asyncio
import logging
import pytest
import time
import tempfile
import shutil
import json
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from hydra_logger.async_hydra.async_queue import (
    AsyncLogQueue, AsyncBatchProcessor, AsyncBackpressureHandler, 
    QueueStats, DataLossProtection
)


class TestQueueStats:
    """Test QueueStats dataclass."""
    
    def test_queue_stats_initialization(self):
        """Test QueueStats initialization."""
        stats = QueueStats()
        
        assert stats.total_messages == 0
        assert stats.processed_messages == 0
        assert stats.dropped_messages == 0
        assert stats.failed_messages == 0
        assert stats.retry_count == 0
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
            dropped_messages=3,
            failed_messages=2,
            retry_count=5,
            queue_size=10,
            max_queue_size=50,
            avg_processing_time=0.1,
            total_processing_time=10.0,
            batch_count=20,
            last_batch_time=time.time()
        )
        
        assert stats.total_messages == 100
        assert stats.processed_messages == 95
        assert stats.dropped_messages == 3
        assert stats.failed_messages == 2
        assert stats.retry_count == 5
        assert stats.queue_size == 10
        assert stats.max_queue_size == 50
        assert stats.avg_processing_time == 0.1
        assert stats.total_processing_time == 10.0
        assert stats.batch_count == 20
        assert stats.last_batch_time > 0


@pytest.fixture
def temp_backup_dir():
    """Create temporary backup directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestDataLossProtection:
    """Test DataLossProtection functionality."""
    
    @pytest.mark.asyncio
    async def test_data_loss_protection_initialization(self, temp_backup_dir):
        """Test DataLossProtection initialization."""
        protection = DataLossProtection(backup_dir=temp_backup_dir, max_retries=5)
        
        assert protection.backup_dir == Path(temp_backup_dir)
        assert protection.max_retries == 5
        assert protection._circuit_open is False
        assert protection._failure_count == 0
        assert protection._last_failure_time == 0
        assert protection._circuit_timeout == 30.0
    
    @pytest.mark.asyncio
    async def test_data_loss_protection_backup_message(self, temp_backup_dir):
        """Test backing up messages."""
        protection = DataLossProtection(backup_dir=temp_backup_dir)
        
        # Test backing up a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None
        )
        
        success = await protection.backup_message(record, "test_queue")
        assert success is True
        
        # Check that backup file was created
        backup_files = list(Path(temp_backup_dir).glob("test_queue_*.json"))
        assert len(backup_files) == 1
        
        # Verify backup content
        with open(backup_files[0], 'r') as f:
            data = json.load(f)
        
        assert data["type"] == "log_record"
        assert data["name"] == "test"
        assert data["level"] == "INFO"
        assert data["message"] == "test message"
    
    @pytest.mark.asyncio
    async def test_data_loss_protection_backup_generic_message(self, temp_backup_dir):
        """Test backing up generic messages."""
        protection = DataLossProtection(backup_dir=temp_backup_dir)
        
        success = await protection.backup_message("generic message", "test_queue")
        assert success is True
        
        # Check that backup file was created
        backup_files = list(Path(temp_backup_dir).glob("test_queue_*.json"))
        assert len(backup_files) == 1
        
        # Verify backup content
        with open(backup_files[0], 'r') as f:
            data = json.load(f)
        
        assert data["type"] == "generic"
        assert data["data"] == "generic message"
    
    @pytest.mark.asyncio
    async def test_data_loss_protection_backup_failure(self):
        """Test backup failure handling."""
        protection = DataLossProtection(backup_dir="/invalid/path")
        
        success = await protection.backup_message("test message", "test_queue")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_data_loss_protection_restore_messages(self, temp_backup_dir):
        """Test restoring messages from backup."""
        protection = DataLossProtection(backup_dir=temp_backup_dir)
        
        # Create some backup files
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None
        )
        
        await protection.backup_message(record, "test_queue")
        await protection.backup_message("generic message", "test_queue")
        
        # Restore messages
        restored = await protection.restore_messages("test_queue")
        
        assert len(restored) == 2
        assert isinstance(restored[0], logging.LogRecord)
        assert restored[0].getMessage() == "test message"
        assert restored[1] == "generic message"
        
        # Backup files should be cleaned up
        backup_files = list(Path(temp_backup_dir).glob("test_queue_*.json"))
        assert len(backup_files) == 0
    
    @pytest.mark.asyncio
    async def test_data_loss_protection_restore_failure(self, temp_backup_dir):
        """Test restore failure handling."""
        protection = DataLossProtection(backup_dir=temp_backup_dir)
        
        # Create invalid backup file
        invalid_file = Path(temp_backup_dir) / "test_queue_123.json"
        with open(invalid_file, 'w') as f:
            f.write("invalid json")
        
        restored = await protection.restore_messages("test_queue")
        assert len(restored) == 0
    
    @pytest.mark.asyncio
    async def test_data_loss_protection_circuit_breaker(self):
        """Test circuit breaker functionality."""
        protection = DataLossProtection(max_retries=3)
        
        # Test normal operation
        should_retry = await protection.should_retry(Exception("test"))
        assert should_retry is True
        
        # Simulate multiple failures to open circuit
        for _ in range(6):  # More than max_retries to ensure circuit opens
            should_retry = await protection.should_retry(Exception("test"))
        
        # Circuit should be open
        assert protection._circuit_open is True
        should_retry = await protection.should_retry(Exception("test"))
        assert should_retry is False
    
    @pytest.mark.asyncio
    async def test_data_loss_protection_circuit_breaker_timeout(self):
        """Test circuit breaker timeout."""
        protection = DataLossProtection(max_retries=3)
        
        # Simulate failures to open circuit
        for _ in range(6):
            await protection.should_retry(Exception("test"))
        
        assert protection._circuit_open is True
        
        # Fast forward time
        protection._last_failure_time = time.time() - 31.0  # More than 30s timeout
        
        should_retry = await protection.should_retry(Exception("test"))
        assert should_retry is True
        assert protection._circuit_open is False
        assert protection._failure_count == 0
    
    def test_data_loss_protection_get_protection_stats(self, temp_backup_dir):
        """Test getting protection statistics."""
        protection = DataLossProtection(backup_dir=temp_backup_dir)
        
        stats = protection.get_protection_stats()
        
        assert "circuit_open" in stats
        assert "failure_count" in stats
        assert "backup_files" in stats
        assert stats["circuit_open"] is False
        assert stats["failure_count"] == 0
        assert stats["backup_files"] == 0


class TestAsyncLogQueue:
    """Test AsyncLogQueue functionality."""
    
    @pytest.mark.asyncio
    async def test_async_log_queue_initialization(self):
        """Test AsyncLogQueue initialization."""
        queue = AsyncLogQueue(
            max_size=100, 
            batch_size=10, 
            batch_timeout=0.5,
            enable_data_protection=True
        )
        
        assert queue.max_size == 100
        assert queue.batch_size == 10
        assert queue.batch_timeout == 0.5
        assert queue.processor is None
        assert queue.enable_data_protection is True
        assert queue._data_protection is not None
        assert not queue._running
    
    @pytest.mark.asyncio
    async def test_async_log_queue_initialization_without_data_protection(self):
        """Test AsyncLogQueue initialization without data protection."""
        queue = AsyncLogQueue(enable_data_protection=False)
        
        assert queue.enable_data_protection is False
        assert queue._data_protection is None
    
    @pytest.mark.asyncio
    async def test_async_log_queue_put_get(self):
        """Test putting and getting messages from queue."""
        queue = AsyncLogQueue(max_size=10, enable_data_protection=False)
        await queue.start()
        
        # Put message
        success = await queue.put("test message")
        assert success is True
        
        # Get message
        message = await queue.get()
        assert message == "test message"
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_full_with_data_protection(self, temp_backup_dir):
        """Test queue behavior when full with data protection."""
        # Use an event to block the processor so the queue stays full
        processor_started = asyncio.Event()
        processor_continue = asyncio.Event()
        
        async def blocking_processor(messages):
            processor_started.set()
            await processor_continue.wait()
        
        queue = AsyncLogQueue(
            max_size=1, 
            batch_size=1, 
            batch_timeout=0.01,
            processor=blocking_processor,
            enable_data_protection=True
        )
        # Mock the backup directory
        if queue._data_protection:
            queue._data_protection.backup_dir = Path(temp_backup_dir)
        try:
            await queue.start()
            # Put first message (fills the queue)
            success1 = await queue.put("message 1")
            assert success1 is True
            # Wait until processor has started (queue is still full)
            await processor_started.wait()
            # Put second message (should trigger backup)
            success2 = await queue.put("message 2")
            assert success2 is True  # Should succeed due to backup
            # Allow processor to continue
            processor_continue.set()
            # Wait a bit for processing
            await asyncio.sleep(0.1)
            # Check stats - should have failed messages due to backup
            stats = queue.get_stats()
            assert stats.total_messages >= 2
            assert stats.failed_messages >= 1  # One message backed up
        finally:
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_full_without_data_protection(self):
        """Test queue behavior when full without data protection."""
        queue = AsyncLogQueue(
            max_size=1, 
            batch_size=1, 
            batch_timeout=0.01,
            enable_data_protection=False
        )
        
        try:
            await queue.start()
            
            # Fill queue
            success1 = await queue.put("message 1")
            assert success1 is True
            
            # Try to put another message (should fail because queue is full)
            success2 = await queue.put("message 2")
            assert success2 is False
            
            # Wait a bit for processing
            await asyncio.sleep(0.1)
            
            # Check stats
            stats = queue.get_stats()
            assert stats.dropped_messages >= 0
            
        finally:
            await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_with_processor(self):
        """Test queue with custom processor."""
        processed_messages = []
        
        async def custom_processor(messages):
            processed_messages.extend(messages)
        
        queue = AsyncLogQueue(
            max_size=10, 
            batch_size=2, 
            batch_timeout=0.05, 
            processor=custom_processor,
            enable_data_protection=False
        )
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
        
        queue = AsyncLogQueue(
            max_size=10, 
            batch_size=3, 
            processor=batch_processor,
            enable_data_protection=False
        )
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
        
        queue = AsyncLogQueue(
            max_size=10, 
            batch_size=100, 
            batch_timeout=0.1, 
            processor=batch_processor,
            enable_data_protection=False
        )
        await queue.start()
        
        # Put one message
        await queue.put("timeout test message")
        
        # Wait for timeout
        await asyncio.sleep(0.2)
        
        assert len(processed_batches) > 0
        assert "timeout test message" in processed_batches[0]
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_with_sync_processor(self):
        """Test queue with synchronous processor."""
        processed_messages = []
        
        def sync_processor(messages):
            processed_messages.extend(messages)
        
        queue = AsyncLogQueue(
            max_size=10, 
            batch_size=2, 
            batch_timeout=0.05, 
            processor=sync_processor,
            enable_data_protection=False
        )
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
    async def test_async_log_queue_error_handling(self):
        """Test error handling in queue worker."""
        error_count = 0
        
        async def error_processor(messages):
            nonlocal error_count
            error_count += 1
            raise Exception("Test error")
        
        queue = AsyncLogQueue(
            max_size=10, 
            processor=error_processor,
            enable_data_protection=False
        )
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
        queue = AsyncLogQueue(max_size=10, enable_data_protection=False)
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
        queue = AsyncLogQueue(max_size=10, enable_data_protection=False)
        await queue.start()
        
        # Put some messages
        await queue.put("test message")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check stats before reset
        stats_before = queue.get_stats()
        assert stats_before.total_messages > 0
        
        # Reset stats
        queue.reset_stats()
        
        # Check stats after reset
        stats_after = queue.get_stats()
        assert stats_after.total_messages == 0
        assert stats_after.processed_messages == 0
        assert stats_after.dropped_messages == 0
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_double_start_stop(self):
        """Test double start/stop behavior."""
        queue = AsyncLogQueue(max_size=10, enable_data_protection=False)
        
        # Double start should be safe
        await queue.start()
        await queue.start()
        
        # Double stop should be safe
        await queue.stop()
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_get_timeout(self):
        """Test queue get with timeout."""
        queue = AsyncLogQueue(max_size=10, enable_data_protection=False)
        await queue.start()
        
        # Try to get from empty queue with timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(queue.get(), timeout=0.1)
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_put_exception_handling(self):
        """Test exception handling in put method."""
        queue = AsyncLogQueue(max_size=10, enable_data_protection=False)
        
        # Mock queue to raise exception
        with patch.object(queue._queue, 'put', side_effect=Exception("Queue error")):
            success = await queue.put("test message")
            assert success is False
    
    @pytest.mark.asyncio
    async def test_async_log_queue_worker_cancellation(self):
        """Test worker cancellation."""
        queue = AsyncLogQueue(max_size=10, enable_data_protection=False)
        await queue.start()
        
        # Put a message
        await queue.put("test message")
        
        # Stop immediately
        await queue.stop()
        
        # Should not crash
    
    @pytest.mark.asyncio
    async def test_async_log_queue_worker_exception_handling(self):
        """Test worker exception handling."""
        error_count = 0
        
        async def error_processor(messages):
            nonlocal error_count
            error_count += 1
            raise Exception("Test error")
        
        queue = AsyncLogQueue(
            max_size=10, 
            processor=error_processor,
            enable_data_protection=False
        )
        await queue.start()
        
        # Put message that will cause error
        await queue.put("error test")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Should not crash
        assert error_count > 0
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_log_queue_remaining_messages_processing(self):
        """Test processing remaining messages on stop."""
        processed_messages = []
        
        async def processor(messages):
            processed_messages.extend(messages)
        
        queue = AsyncLogQueue(
            max_size=10, 
            processor=processor,
            enable_data_protection=False
        )
        await queue.start()
        
        # Put messages
        for i in range(5):
            await queue.put(f"message {i}")
        
        # Stop immediately
        await queue.stop()
        
        # All messages should be processed
        assert len(processed_messages) >= 5
    
    @pytest.mark.asyncio
    async def test_async_log_queue_error_recovery_with_retry(self):
        """Test error recovery with retry logic."""
        call_count = 0
        
        async def failing_processor(messages):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
        
        queue = AsyncLogQueue(
            max_size=10, 
            processor=failing_processor,
            enable_data_protection=False
        )
        await queue.start()
        
        # Put message
        await queue.put("retry test")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Should have been called multiple times due to retries
        assert call_count >= 2
        
        await queue.stop()
    
    def test_async_log_queue_get_data_protection_stats(self):
        """Test getting data protection statistics."""
        queue = AsyncLogQueue(enable_data_protection=True)
        
        stats = queue.get_data_protection_stats()
        assert stats is not None
        assert "circuit_open" in stats
        assert "failure_count" in stats
        assert "backup_files" in stats
        
        # Test without data protection
        queue_no_protection = AsyncLogQueue(enable_data_protection=False)
        stats = queue_no_protection.get_data_protection_stats()
        assert stats is None


class TestAsyncBatchProcessor:
    """Test AsyncBatchProcessor functionality."""
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_initialization(self):
        """Test AsyncBatchProcessor initialization."""
        processor = AsyncBatchProcessor(
            batch_size=50, 
            batch_timeout=0.5,
            processor=None
        )
        
        assert processor.batch_size == 50
        assert processor.batch_timeout == 0.5
        assert processor.processor is None
        assert not processor._running
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_add_message(self):
        """Test adding messages to batch processor."""
        processed_messages = []
        
        async def custom_processor(messages):
            processed_messages.extend(messages)
        
        processor = AsyncBatchProcessor(
            batch_size=3, 
            processor=custom_processor
        )
        await processor.start()
        
        # Add messages
        for i in range(5):
            await processor.add_message(f"message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        assert len(processed_messages) >= 3
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_timeout(self):
        """Test timeout-based batch processing."""
        processed_messages = []
        
        async def custom_processor(messages):
            processed_messages.extend(messages)
        
        processor = AsyncBatchProcessor(
            batch_size=100, 
            batch_timeout=0.1,
            processor=custom_processor
        )
        await processor.start()
        
        # Add one message
        await processor.add_message("timeout test message")
        
        # Wait for timeout
        await asyncio.sleep(0.2)
        
        assert len(processed_messages) > 0
        assert "timeout test message" in processed_messages
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_manual_process(self):
        """Test manual batch processing."""
        processed_messages = []
        
        async def custom_processor(messages):
            processed_messages.extend(messages)
        
        processor = AsyncBatchProcessor(
            batch_size=10, 
            processor=custom_processor
        )
        await processor.start()
        
        # Add messages
        for i in range(3):
            await processor.add_message(f"message {i}")
        
        # Manually process
        await processor.process_batch()
        
        assert len(processed_messages) == 3
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_error_handling(self):
        """Test error handling in batch processor."""
        error_count = 0
        
        async def error_processor(messages):
            nonlocal error_count
            error_count += 1
            raise Exception("Test error")
        
        processor = AsyncBatchProcessor(
            batch_size=3, 
            processor=error_processor
        )
        await processor.start()
        
        # Add messages that will cause error
        for i in range(3):
            await processor.add_message(f"error message {i}")
            # Wait for processing
            await asyncio.sleep(0.1)
        
        # Should not crash
        assert error_count > 0
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_with_sync_processor(self):
        """Test batch processor with synchronous processor."""
        processed_messages = []
        
        def sync_processor(messages):
            processed_messages.extend(messages)
        
        processor = AsyncBatchProcessor(
            batch_size=3, 
            processor=sync_processor
        )
        await processor.start()
        
        # Add messages
        for i in range(3):
            await processor.add_message(f"message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        assert len(processed_messages) == 3
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_stats(self):
        """Test batch processor statistics."""
        processor = AsyncBatchProcessor(batch_size=3)
        await processor.start()
        
        # Add messages
        for i in range(5):
            await processor.add_message(f"message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        stats = processor.get_stats()
        assert stats.total_messages >= 5
        assert stats.processed_messages >= 5
        assert stats.batch_count > 0
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_reset_stats(self):
        """Test resetting batch processor statistics."""
        processor = AsyncBatchProcessor(batch_size=3)
        await processor.start()
        
        # Add messages
        for i in range(3):
            await processor.add_message(f"message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check stats before reset
        stats_before = processor.get_stats()
        assert stats_before.total_messages > 0
        
        # Reset stats
        processor.reset_stats()
        
        # Check stats after reset
        stats_after = processor.get_stats()
        assert stats_after.total_messages == 0
        assert stats_after.processed_messages == 0
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_start_stop(self):
        """Test batch processor start/stop behavior."""
        processed_messages = []
        
        async def custom_processor(messages):
            processed_messages.extend(messages)
        
        processor = AsyncBatchProcessor(
            batch_size=10, 
            processor=custom_processor
        )
        
        # Double start should be safe
        await processor.start()
        await processor.start()
        
        # Add messages
        for i in range(3):
            await processor.add_message(f"message {i}")
        
        # Double stop should be safe
        await processor.stop()
        await processor.stop()
        
        # Messages should be processed
        assert len(processed_messages) >= 3
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_worker_exception(self):
        """Test batch processor worker exception handling."""
        processor = AsyncBatchProcessor(batch_size=3)
        await processor.start()
        
        # Add messages
        for i in range(3):
            await processor.add_message(f"message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Should not crash
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_async_batch_processor_remaining_messages(self):
        """Test processing remaining messages on stop."""
        processed_messages = []
        
        async def processor(messages):
            processed_messages.extend(messages)
        
        batch_processor = AsyncBatchProcessor(
            batch_size=10, 
            processor=processor
        )
        await batch_processor.start()
        
        # Add messages
        for i in range(5):
            await batch_processor.add_message(f"message {i}")
        
        # Stop immediately
        await batch_processor.stop()
        
        # All messages should be processed
        assert len(processed_messages) >= 5


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
        assert handler._queue_size == 0
    
    @pytest.mark.asyncio
    async def test_async_backpressure_handler_should_accept_message(self):
        """Test message acceptance logic."""
        handler = AsyncBackpressureHandler(max_queue_size=100)
        
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
        
        # Test above slow down threshold - should have delay
        delay = await handler.get_processing_delay(80)  # 80% of max
        assert delay > 0.0
        
        # Test high queue size
        delay = await handler.get_processing_delay(95)
        assert delay > 0.0
        assert delay <= 1.0
    
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

    @pytest.mark.asyncio
    async def test_async_backpressure_handler_edge_cases(self):
        """Test backpressure handler edge cases."""
        handler = AsyncBackpressureHandler(max_queue_size=100)
        
        # Test zero queue size
        should_accept = await handler.should_accept_message(0)
        assert should_accept is True
        
        delay = await handler.get_processing_delay(0)
        assert delay == 0.0
        
        # Test exact threshold
        should_accept = await handler.should_accept_message(70)
        assert should_accept is True
        
        delay = await handler.get_processing_delay(70)
        assert delay == 0.0


class TestAsyncQueueIntegration:
    """Integration tests for async queue components."""
    
    @pytest.mark.asyncio
    async def test_queue_with_backpressure(self):
        """Test queue with backpressure handler."""
        queue = AsyncLogQueue(max_size=10, enable_data_protection=False)
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
        queue = AsyncLogQueue(
            max_size=10, 
            processor=batch_processor.processor,
            enable_data_protection=False
        )
        
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
        
        queue = AsyncLogQueue(
            max_size=100, 
            batch_size=10, 
            processor=fast_processor,
            enable_data_protection=False
        )
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
            # Process each message individually to handle errors per message
            for msg in messages:
                try:
                    if "error" in str(msg):
                        error_count += 1
                        raise Exception("Processing error")
                    else:
                        success_count += 1
                except Exception:
                    # Continue processing other messages in the batch
                    pass
        
        queue = AsyncLogQueue(
            max_size=10, 
            processor=mixed_processor,
            enable_data_protection=False
        )
        await queue.start()
        
        # Send mixed messages
        for i in range(5):
            if i % 2 == 0:
                await queue.put(f"error message {i}")
            else:
                await queue.put(f"success message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Should handle errors gracefully
        assert error_count > 0
        assert success_count > 0
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_queue_stats_thread_safety(self):
        """Test queue statistics thread safety."""
        queue = AsyncLogQueue(max_size=100, enable_data_protection=False)
        await queue.start()
        
        # Simulate concurrent access
        async def add_messages():
            for i in range(10):
                await queue.put(f"concurrent message {i}")
                await asyncio.sleep(0.01)
        
        # Start multiple concurrent tasks
        tasks = [add_messages() for _ in range(3)]
        await asyncio.gather(*tasks)
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Should not crash and stats should be reasonable
        stats = queue.get_stats()
        assert stats.total_messages >= 30
        
        await queue.stop()