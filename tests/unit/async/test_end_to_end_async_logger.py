"""
End-to-end async logging integration tests for Hydra-Logger.

Covers:
- Multiple handler types (file, console, composite)
- Context and distributed tracing
- Log delivery and ordering
- Graceful shutdown and resource cleanup
- Data integrity and no data loss
"""

import asyncio
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from hydra_logger.async_hydra import (
    AsyncHydraLogger,
    AsyncFileHandler,
    AsyncConsoleHandler,
    AsyncCompositeHandler,
    async_context,
    trace_context,
    span_context
)


@pytest.fixture(scope="function")
def test_logs_dir():
    """Create temporary test logs directory."""
    test_dir = tempfile.mkdtemp(prefix="hydra_e2e_test_")
    yield test_dir
    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_end_to_end_logging(test_logs_dir, capsys):
    """Test end-to-end async logging with all features enabled."""
    log_file = os.path.join(test_logs_dir, "test_e2e_async.log")
    
    config = {
        'handlers': [
            {'type': 'file', 'filename': log_file},
            {'type': 'console', 'use_colors': False},
            {
                'type': 'composite',
                'parallel_execution': True,
                'fail_fast': False,
                'handlers': [
                    {'type': 'file', 'filename': log_file},
                    {'type': 'console', 'use_colors': False}
                ]
            }
        ]
    }
    logger = AsyncHydraLogger(config)
    await logger.initialize()

    # Log with context and tracing
    async with async_context() as ctx_mgr:
        ctx_mgr.update_context_metadata('user_id', 'e2e_user')
        async with trace_context("e2e_trace", "e2e_corr") as trace:
            async with span_context("e2e_span") as span_id:
                for i in range(10):
                    await logger.info("E2E", f"End-to-end message {i}")

    # Allow time for async writers to flush
    await asyncio.sleep(0.5)
    await logger.aclose()

    # Validate file output
    assert os.path.exists(log_file)
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        # Each message is logged to file handler and composite file handler
        assert len(lines) >= 20
        assert any("End-to-end message 0" in line for line in lines)
        assert any("End-to-end message 9" in line for line in lines)

    # Validate console output (captured)
    captured = capsys.readouterr()
    assert "End-to-end message 0" in captured.err or "End-to-end message 0" in captured.out
    assert "End-to-end message 9" in captured.err or "End-to-end message 9" in captured.out

    # Validate logger health
    assert logger.is_healthy()
    assert logger.is_performance_healthy()

    # Validate no data loss (all messages present)
    for i in range(10):
        assert any(f"End-to-end message {i}" in line for line in lines) 