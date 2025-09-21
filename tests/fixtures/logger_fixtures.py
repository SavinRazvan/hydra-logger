"""
Logger test fixtures for Hydra-Logger.

Provides common logger instances and configurations for testing.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from hydra_logger import (
    SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger
)



@pytest.fixture
def sync_logger():
    """Basic sync logger fixture."""
    logger = SyncLogger()
    yield logger
    logger.close()


@pytest.fixture
def async_logger():
    """Basic async logger fixture."""
    logger = AsyncLogger()
    yield logger
    asyncio.run(logger.aclose())


@pytest.fixture
def composite_logger():
    """Composite logger fixture."""
    logger = CompositeLogger()
    yield logger
    logger.close()


@pytest.fixture
def composite_async_logger():
    """Composite async logger fixture."""
    logger = CompositeAsyncLogger()
    yield logger
    asyncio.run(logger.aclose())


@pytest.fixture
def all_sync_loggers():
    """All sync logger fixtures."""
    return {
        'sync': SyncLogger(),
        'composite': CompositeLogger()
    }


@pytest.fixture
def all_async_loggers():
    """All async logger fixtures."""
    return {
        'async': AsyncLogger(),
        'composite_async': CompositeAsyncLogger()
    }


@pytest.fixture
def all_loggers():
    """All logger fixtures (sync and async)."""
    return {
        'sync': SyncLogger(),
        'async': AsyncLogger(),
        'composite': CompositeLogger(),
        'composite_async': CompositeAsyncLogger()
    }


@pytest.fixture
def logger_configs():
    """Common logger configurations for testing."""
    return {
        'minimal': {
            'layers': {
                'default': {
                    'level': 'INFO',
                    'destinations': [{
                        'type': 'console',
                        'format': 'plain-text',
                        'use_colors': False
                    }]
                }
            }
        },
        'with_file': {
            'layers': {
                'default': {
                    'level': 'INFO',
                    'destinations': [
                        {
                            'type': 'console',
                            'format': 'colored',
                            'use_colors': True
                        },
                        {
                            'type': 'file',
                            'path': 'test.log',
                            'format': 'json-lines'
                        }
                    ]
                }
            }
        },
        'performance': {
            'layers': {
                'default': {
                    'level': 'INFO',
                    'destinations': [{
                        'type': 'console',
                        'format': 'plain-text',
                        'use_colors': False,
                        'buffer_size': 1000,
                        'flush_interval': 0.1
                    }]
                }
            }
        }
    }
