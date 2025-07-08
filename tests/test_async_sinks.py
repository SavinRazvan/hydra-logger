"""
Tests for async sinks functionality.

This module tests the async sinks including AsyncHttpSink, AsyncDatabaseSink,
AsyncQueueSink, and AsyncCloudSink.
"""

import asyncio
import logging
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from hydra_logger.async_hydra.async_sinks import (
    AsyncSink, AsyncHttpSink, AsyncDatabaseSink, AsyncQueueSink, AsyncCloudSink, SinkStats
)

# Dummy concrete subclass for testing abstract AsyncSink
class DummyAsyncSink(AsyncSink):
    async def emit_async(self, record):
        pass

class TestAsyncSink:
    """Test base AsyncSink functionality."""
    
    def test_async_sink_initialization(self):
        """Test AsyncSink initialization."""
        sink = DummyAsyncSink(retry_count=5, retry_delay=2.0)
        
        assert sink._retry_count == 5
        assert sink._retry_delay == 2.0
        assert isinstance(sink._stats, SinkStats)
    
    def test_async_sink_get_stats(self):
        """Test getting sink statistics."""
        sink = DummyAsyncSink()
        
        stats = sink.get_stats()
        assert isinstance(stats, SinkStats)
        assert stats.total_messages == 0
        assert stats.successful_messages == 0
        assert stats.failed_messages == 0
    
    def test_async_sink_reset_stats(self):
        """Test resetting sink statistics."""
        sink = DummyAsyncSink()
        
        # Modify stats
        sink._stats.total_messages = 10
        sink._stats.successful_messages = 8
        sink._stats.failed_messages = 2
        
        # Reset stats
        sink.reset_stats()
        
        # Check stats are reset
        stats = sink.get_stats()
        assert stats.total_messages == 0
        assert stats.successful_messages == 0
        assert stats.failed_messages == 0
    
    @pytest.mark.asyncio
    async def test_async_sink_record_success(self):
        """Test recording successful operations."""
        sink = DummyAsyncSink()
        
        await sink._record_success(0.1)
        
        stats = sink.get_stats()
        assert stats.total_messages == 1
        assert stats.successful_messages == 1
        assert stats.failed_messages == 0
        assert stats.avg_response_time == 0.1
    
    @pytest.mark.asyncio
    async def test_async_sink_record_failure(self):
        """Test recording failed operations."""
        sink = DummyAsyncSink()
        
        await sink._record_failure("Test error", 0.05)
        
        stats = sink.get_stats()
        assert stats.total_messages == 1
        assert stats.successful_messages == 0
        assert stats.failed_messages == 1
        assert stats.last_error == "Test error"
    
    @pytest.mark.asyncio
    async def test_async_sink_record_retry(self):
        """Test recording retry operations."""
        sink = DummyAsyncSink()
        
        await sink._record_retry()
        
        stats = sink.get_stats()
        assert stats.retry_count == 1
    
    @pytest.mark.asyncio
    async def test_async_sink_record_connection_error(self):
        """Test recording connection errors."""
        sink = DummyAsyncSink()
        
        await sink._record_connection_error()
        
        stats = sink.get_stats()
        assert stats.connection_errors == 1
        assert stats.last_error is not None and "Connection error" in stats.last_error


class TestAsyncHttpSink:
    """Test AsyncHttpSink functionality."""
    
    @pytest.mark.asyncio
    async def test_async_http_sink_initialization(self):
        """Test AsyncHttpSink initialization."""
        sink = AsyncHttpSink(
            url="https://example.com/logs",
            method="POST",
            headers={"Content-Type": "application/json"},
            timeout=30.0,
            retry_count=3,
            retry_delay=1.0,
            max_connections=10
        )
        
        assert sink.url == "https://example.com/logs"
        assert sink.method == "POST"
        assert sink.headers == {"Content-Type": "application/json"}
        assert sink.timeout == 30.0
        assert sink.max_connections == 10
    
    @pytest.mark.asyncio
    async def test_async_http_sink_emit_async_success(self):
        """Test successful HTTP sink emission."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOHTTP_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.aiohttp') as mock_aiohttp:
                # Mock session and response
                mock_session = AsyncMock()
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="OK")
                mock_session.post = AsyncMock(return_value=mock_response)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                
                mock_aiohttp.ClientSession.return_value = mock_session
                
                sink = AsyncHttpSink(url="https://example.com/logs")
                
                # Create test record
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg="Test HTTP log message",
                    args=(),
                    exc_info=None
                )
                
                # Test emission
                result = await sink.emit_async(record)
                
                assert result is True
                assert mock_session.post.called
                
                # Check stats
                stats = sink.get_stats()
                assert stats.successful_messages == 1
                assert stats.failed_messages == 0
    
    @pytest.mark.asyncio
    async def test_async_http_sink_emit_async_failure(self):
        """Test failed HTTP sink emission."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOHTTP_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.aiohttp') as mock_aiohttp:
                # Mock session that raises exception
                mock_session = AsyncMock()
                mock_session.post = AsyncMock(side_effect=Exception("Connection error"))
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                
                mock_aiohttp.ClientSession.return_value = mock_session
                
                sink = AsyncHttpSink(url="https://example.com/logs")
                
                # Create test record
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg="Test HTTP log message",
                    args=(),
                    exc_info=None
                )
                
                # Test emission
                result = await sink.emit_async(record)
                
                assert result is False
                
                # Check stats
                stats = sink.get_stats()
                assert stats.successful_messages == 0
                assert stats.failed_messages == 1
                assert stats.last_error is not None and "Connection error" in stats.last_error
    
    @pytest.mark.asyncio
    async def test_async_http_sink_emit_async_without_aiohttp(self):
        """Test HTTP sink without aiohttp available."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOHTTP_AVAILABLE', False):
            sink = AsyncHttpSink(url="https://example.com/logs")
            
            # Create test record
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test HTTP log message",
                args=(),
                exc_info=None
            )
            
            # Test emission (should fail gracefully)
            result = await sink.emit_async(record)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_async_http_sink_close(self):
        """Test HTTP sink close functionality."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOHTTP_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.aiohttp') as mock_aiohttp:
                mock_session = AsyncMock()
                mock_aiohttp.ClientSession.return_value = mock_session
                
                sink = AsyncHttpSink(url="https://example.com/logs")
                sink._session = mock_session
                
                # Test close
                await sink.close()
                
                assert mock_session.close.called


class TestAsyncDatabaseSink:
    """Test AsyncDatabaseSink functionality."""
    
    @pytest.mark.asyncio
    async def test_async_database_sink_initialization(self):
        """Test AsyncDatabaseSink initialization."""
        sink = AsyncDatabaseSink(
            connection_string="postgresql://user:pass@localhost/db",
            table_name="logs",
            retry_count=3,
            retry_delay=1.0,
            max_connections=5
        )
        
        assert sink.connection_string == "postgresql://user:pass@localhost/db"
        assert sink.table_name == "logs"
        assert sink.max_connections == 5
    
    @pytest.mark.asyncio
    async def test_async_database_sink_emit_async_success(self):
        """Test successful database sink emission."""
        with patch('hydra_logger.async_hydra.async_sinks.ASYNCPG_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.asyncpg') as mock_asyncpg:
                # Mock pool and connection
                mock_pool = AsyncMock()
                mock_connection = AsyncMock()
                mock_pool.acquire = AsyncMock(return_value=mock_connection)
                mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
                mock_connection.__aexit__ = AsyncMock(return_value=None)
                mock_connection.execute = AsyncMock()
                
                mock_asyncpg.create_pool.return_value = mock_pool
                
                sink = AsyncDatabaseSink(connection_string="postgresql://localhost/db")
                
                # Create test record
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg="Test database log message",
                    args=(),
                    exc_info=None
                )
                
                # Test emission
                result = await sink.emit_async(record)
                
                assert result is True
                assert mock_connection.execute.called
    
    @pytest.mark.asyncio
    async def test_async_database_sink_emit_async_failure(self):
        """Test failed database sink emission."""
        with patch('hydra_logger.async_hydra.async_sinks.ASYNCPG_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.asyncpg') as mock_asyncpg:
                # Mock pool that raises exception
                mock_pool = AsyncMock()
                mock_pool.acquire = AsyncMock(side_effect=Exception("Database error"))
                
                mock_asyncpg.create_pool.return_value = mock_pool
                
                sink = AsyncDatabaseSink(connection_string="postgresql://localhost/db")
                
                # Create test record
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg="Test database log message",
                    args=(),
                    exc_info=None
                )
                
                # Test emission
                result = await sink.emit_async(record)
                
                assert result is False
                
                # Check stats
                stats = sink.get_stats()
                assert stats.failed_messages == 1
                assert stats.last_error is not None and "Database error" in stats.last_error
    
    @pytest.mark.asyncio
    async def test_async_database_sink_emit_async_without_asyncpg(self):
        """Test database sink without asyncpg available."""
        with patch('hydra_logger.async_hydra.async_sinks.ASYNCPG_AVAILABLE', False):
            sink = AsyncDatabaseSink(connection_string="postgresql://localhost/db")
            
            # Create test record
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test database log message",
                args=(),
                exc_info=None
            )
            
            # Test emission (should fail gracefully)
            result = await sink.emit_async(record)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_async_database_sink_close(self):
        """Test database sink close functionality."""
        with patch('hydra_logger.async_hydra.async_sinks.ASYNCPG_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.asyncpg') as mock_asyncpg:
                mock_pool = AsyncMock()
                mock_asyncpg.create_pool.return_value = mock_pool
                
                sink = AsyncDatabaseSink(connection_string="postgresql://localhost/db")
                sink._pool = mock_pool
                
                # Test close
                await sink.close()
                
                assert mock_pool.close.called


class TestAsyncQueueSink:
    """Test AsyncQueueSink functionality."""
    
    @pytest.mark.asyncio
    async def test_async_queue_sink_initialization(self):
        """Test AsyncQueueSink initialization."""
        sink = AsyncQueueSink(
            queue_url="redis://localhost:6379",
            queue_name="logs",
            retry_count=3,
            retry_delay=1.0,
            max_connections=5
        )
        
        assert sink.queue_url == "redis://localhost:6379"
        assert sink.queue_name == "logs"
        assert sink.max_connections == 5
    
    @pytest.mark.asyncio
    async def test_async_queue_sink_emit_async_success(self):
        """Test successful queue sink emission."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOREDIS_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.aioredis') as mock_aioredis:
                # Mock Redis connection
                mock_redis = AsyncMock()
                mock_redis.lpush = AsyncMock(return_value=1)
                mock_redis.close = AsyncMock()
                
                mock_aioredis.from_url.return_value = mock_redis
                
                sink = AsyncQueueSink(queue_url="redis://localhost:6379")
                
                # Create test record
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg="Test queue log message",
                    args=(),
                    exc_info=None
                )
                
                # Test emission
                result = await sink.emit_async(record)
                
                assert result is True
                assert mock_redis.lpush.called
    
    @pytest.mark.asyncio
    async def test_async_queue_sink_emit_async_failure(self):
        """Test failed queue sink emission."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOREDIS_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.aioredis') as mock_aioredis:
                # Mock Redis connection that raises exception
                mock_redis = AsyncMock()
                mock_redis.lpush = AsyncMock(side_effect=Exception("Redis error"))
                mock_redis.close = AsyncMock()
                
                mock_aioredis.from_url.return_value = mock_redis
                
                sink = AsyncQueueSink(queue_url="redis://localhost:6379")
                
                # Create test record
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg="Test queue log message",
                    args=(),
                    exc_info=None
                )
                
                # Test emission
                result = await sink.emit_async(record)
                
                assert result is False
                
                # Check stats
                stats = sink.get_stats()
                assert stats.failed_messages == 1
                assert stats.last_error is not None and "Redis error" in stats.last_error
    
    @pytest.mark.asyncio
    async def test_async_queue_sink_emit_async_without_aioredis(self):
        """Test queue sink without aioredis available."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOREDIS_AVAILABLE', False):
            sink = AsyncQueueSink(queue_url="redis://localhost:6379")
            
            # Create test record
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test queue log message",
                args=(),
                exc_info=None
            )
            
            # Test emission (should fail gracefully)
            result = await sink.emit_async(record)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_async_queue_sink_close(self):
        """Test queue sink close functionality."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOREDIS_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.aioredis') as mock_aioredis:
                mock_redis = AsyncMock()
                mock_aioredis.from_url.return_value = mock_redis
                
                sink = AsyncQueueSink(queue_url="redis://localhost:6379")
                sink._redis = mock_redis
                
                # Test close
                await sink.close()
                
                assert mock_redis.close.called


class TestAsyncCloudSink:
    """Test AsyncCloudSink functionality."""
    
    @pytest.mark.asyncio
    async def test_async_cloud_sink_initialization(self):
        """Test AsyncCloudSink initialization."""
        credentials = {
            "access_key": "test_key",
            "secret_key": "test_secret",
            "region": "us-east-1"
        }
        
        sink = AsyncCloudSink(
            service_type="aws",
            credentials=credentials,
            retry_count=3,
            retry_delay=1.0
        )
        
        assert sink.service_type == "aws"
        assert sink.credentials == credentials
    
    @pytest.mark.asyncio
    async def test_async_cloud_sink_emit_async_aws(self):
        """Test AWS cloud sink emission."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOHTTP_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.aiohttp') as mock_aiohttp:
                # Mock session and response
                mock_session = AsyncMock()
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="OK")
                mock_session.post = AsyncMock(return_value=mock_response)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                
                mock_aiohttp.ClientSession.return_value = mock_session
                
                credentials = {
                    "access_key": "test_key",
                    "secret_key": "test_secret",
                    "region": "us-east-1"
                }
                
                sink = AsyncCloudSink(service_type="aws", credentials=credentials)
                
                # Create test record
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg="Test AWS cloud log message",
                    args=(),
                    exc_info=None
                )
                
                # Test emission
                result = await sink.emit_async(record)
                
                assert result is True
                assert mock_session.post.called
    
    @pytest.mark.asyncio
    async def test_async_cloud_sink_emit_async_gcp(self):
        """Test GCP cloud sink emission."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOHTTP_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.aiohttp') as mock_aiohttp:
                # Mock session and response
                mock_session = AsyncMock()
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="OK")
                mock_session.post = AsyncMock(return_value=mock_response)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                
                mock_aiohttp.ClientSession.return_value = mock_session
                
                credentials = {
                    "project_id": "test-project",
                    "private_key": "test-key"
                }
                
                sink = AsyncCloudSink(service_type="gcp", credentials=credentials)
                
                # Create test record
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg="Test GCP cloud log message",
                    args=(),
                    exc_info=None
                )
                
                # Test emission
                result = await sink.emit_async(record)
                
                assert result is True
                assert mock_session.post.called
    
    @pytest.mark.asyncio
    async def test_async_cloud_sink_emit_async_azure(self):
        """Test Azure cloud sink emission."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOHTTP_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.aiohttp') as mock_aiohttp:
                # Mock session and response
                mock_session = AsyncMock()
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="OK")
                mock_session.post = AsyncMock(return_value=mock_response)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                
                mock_aiohttp.ClientSession.return_value = mock_session
                
                credentials = {
                    "connection_string": "test-connection",
                    "account_name": "test-account"
                }
                
                sink = AsyncCloudSink(service_type="azure", credentials=credentials)
                
                # Create test record
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=1,
                    msg="Test Azure cloud log message",
                    args=(),
                    exc_info=None
                )
                
                # Test emission
                result = await sink.emit_async(record)
                
                assert result is True
                assert mock_session.post.called
    
    @pytest.mark.asyncio
    async def test_async_cloud_sink_emit_async_unsupported_service(self):
        """Test cloud sink with unsupported service type."""
        credentials = {"test": "value"}
        
        sink = AsyncCloudSink(service_type="unsupported", credentials=credentials)
        
        # Create test record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test unsupported cloud log message",
            args=(),
            exc_info=None
        )
        
        # Test emission (should fail gracefully)
        result = await sink.emit_async(record)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_async_cloud_sink_close(self):
        """Test cloud sink close functionality."""
        with patch('hydra_logger.async_hydra.async_sinks.AIOHTTP_AVAILABLE', True):
            with patch('hydra_logger.async_hydra.async_sinks.aiohttp') as mock_aiohttp:
                mock_session = AsyncMock()
                mock_aiohttp.ClientSession.return_value = mock_session
                
                credentials = {"test": "value"}
                sink = AsyncCloudSink(service_type="aws", credentials=credentials)
                sink._session = mock_session
                
                # Test close
                await sink.close()
                
                assert mock_session.close.called


class TestSinkStats:
    """Test SinkStats dataclass."""
    
    def test_sink_stats_initialization(self):
        """Test SinkStats initialization."""
        stats = SinkStats()
        
        assert stats.total_messages == 0
        assert stats.successful_messages == 0
        assert stats.failed_messages == 0
        assert stats.retry_count == 0
        assert stats.avg_response_time == 0.0
        assert stats.total_response_time == 0.0
        assert stats.connection_errors == 0
        assert stats.last_error is None
    
    def test_sink_stats_with_values(self):
        """Test SinkStats with custom values."""
        stats = SinkStats(
            total_messages=100,
            successful_messages=95,
            failed_messages=5,
            retry_count=3,
            avg_response_time=0.1,
            total_response_time=10.0,
            connection_errors=2,
            last_error="Test error"
        )
        
        assert stats.total_messages == 100
        assert stats.successful_messages == 95
        assert stats.failed_messages == 5
        assert stats.retry_count == 3
        assert stats.avg_response_time == 0.1
        assert stats.total_response_time == 10.0
        assert stats.connection_errors == 2
        assert stats.last_error == "Test error"


class TestAsyncSinksIntegration:
    """Integration tests for async sinks."""
    
    @pytest.mark.asyncio
    async def test_multiple_sinks_concurrent_emission(self):
        """Test concurrent emission to multiple sinks."""
        # Create mock sinks
        http_sink = Mock()
        http_sink.emit_async = AsyncMock(return_value=True)
        
        db_sink = Mock()
        db_sink.emit_async = AsyncMock(return_value=True)
        
        queue_sink = Mock()
        queue_sink.emit_async = AsyncMock(return_value=True)
        
        # Create test record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test concurrent emission",
            args=(),
            exc_info=None
        )
        
        # Emit to all sinks concurrently
        tasks = [
            http_sink.emit_async(record),
            db_sink.emit_async(record),
            queue_sink.emit_async(record)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check all sinks were called
        assert all(result is True for result in results)
        assert http_sink.emit_async.called
        assert db_sink.emit_async.called
        assert queue_sink.emit_async.called
    
    @pytest.mark.asyncio
    async def test_sink_error_recovery(self):
        """Test sink error recovery."""
        # Create sink that fails initially then succeeds
        fail_count = 0
        
        async def failing_emit(record):
            nonlocal fail_count
            if fail_count < 2:
                fail_count += 1
                raise Exception("Temporary failure")
            return True
        
        sink = Mock()
        sink.emit_async = AsyncMock(side_effect=failing_emit)
        
        # Create test record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test error recovery",
            args=(),
            exc_info=None
        )
        
        # Should eventually succeed
        result = await sink.emit_async(record)
        assert result is True
        assert fail_count == 2
    
    @pytest.mark.asyncio
    async def test_sink_performance_under_load(self):
        """Test sink performance under load."""
        # Create fast mock sink
        async def fast_emit(record):
            await asyncio.sleep(0.001)  # Very fast
            return True
        
        sink = Mock()
        sink.emit_async = AsyncMock(side_effect=fast_emit)
        
        # Create test records
        records = [
            logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg=f"Load test message {i}",
                args=(),
                exc_info=None
            )
            for i in range(100)
        ]
        
        # Emit all records concurrently
        start_time = asyncio.get_event_loop().time()
        
        tasks = [sink.emit_async(record) for record in records]
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        # Should process quickly
        assert processing_time < 1.0
        assert all(result is True for result in results)
        assert len(results) == 100 