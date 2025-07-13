import pytest
from hydra_logger.async_hydra import AsyncHydraLogger

class TestSyncLogger:
    def test_sync_close(self):
        """Test synchronous close method for AsyncHydraLogger."""
        logger = AsyncHydraLogger()
        logger.close()
        # Should not raise any exceptions
        assert True 