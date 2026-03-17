"""
Role: Apply optional extension processing in logger pipeline.
Used By:
 - `hydra_logger.loggers.sync_logger`
 - `hydra_logger.loggers.async_logger`
Depends On:
 - hydra_logger
Notes:
 - Keeps extension handling isolated from logger orchestration flow.
"""

import logging
import json
import time
import uuid

from ...types.records import LogRecord


_logger = logging.getLogger(__name__)
_DEBUG_LOG_PATH = "/home/razvansavin/Projects/hydra-logger/.cursor/debug-48bb46.log"
_DEBUG_SESSION_ID = "48bb46"


# region agent log
def _agent_log(run_id: str, hypothesis_id: str, message: str, data: dict) -> None:
    try:
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "sessionId": _DEBUG_SESSION_ID,
                        "runId": run_id,
                        "hypothesisId": hypothesis_id,
                        "id": f"log_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}",
                        "location": "hydra_logger/loggers/pipeline/extension_processor.py:apply_data_protection",
                        "message": message,
                        "data": data,
                        "timestamp": int(time.time() * 1000),
                    },
                    default=str,
                )
                + "\n"
            )
    except Exception:
        pass


# endregion


class ExtensionProcessor:
    """Apply enabled extension processors to log records."""

    def apply_data_protection(self, record: LogRecord, data_protection) -> LogRecord:
        """Apply data-protection extension to record message when enabled."""
        original_message = record.message
        if data_protection and data_protection.is_enabled():
            try:
                record.message = data_protection.process(record.message)
                # region agent log
                _agent_log(
                    run_id="pre-fix",
                    hypothesis_id="H1",
                    message="Data protection processed message",
                    data={
                        "changed": original_message != record.message,
                        "contains_password_after": "password=" in record.message.lower(),
                        "contains_token_after": "token=" in record.message.lower(),
                    },
                )
                # endregion
            except Exception:
                _logger.exception(
                    "Data protection extension failed for type=%s",
                    type(data_protection).__name__,
                )
        else:
            # region agent log
            _agent_log(
                run_id="pre-fix",
                hypothesis_id="H1",
                message="Data protection disabled or unavailable",
                data={
                    "has_data_protection": data_protection is not None,
                    "is_enabled": bool(
                        data_protection and getattr(data_protection, "is_enabled", lambda: False)()
                    ),
                },
            )
            # endregion
        return record
