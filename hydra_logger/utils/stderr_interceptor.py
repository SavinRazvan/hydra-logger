"""
Role: Implements hydra_logger.utils.stderr_interceptor functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - hydra_logger
 - os
 - sys
Notes:
 - Intercepts stderr writes and forwards structured error output to logger sinks.
"""

import sys

from .error_logger import log_error_message


class StderrInterceptor:
    """
    Intercepts stderr to capture tracemalloc and other system errors
    that are printed but don't raise exceptions.
    """

    _original_stderr = None
    _intercepting = False
    _error_keywords = ["tracemalloc", "memory", "malloc", "allocation", "failed"]

    @classmethod
    def start_intercepting(cls) -> None:
        """Start intercepting stderr output."""
        if cls._intercepting:
            return

        cls._original_stderr = sys.stderr
        cls._intercepting = True

        # Create a wrapper that captures and forwards
        class InterceptingStderr:
            def __init__(self, original):
                self.original = original
                self.buffer = []

            def write(self, text: str) -> None:
                # Always forward to original stderr first (so user sees it immediately)
                self.original.write(text)

                # Then check if we should log it
                text_stripped = text.strip()
                if text_stripped:
                    self.buffer.append(text)
                    # Check if this looks like an error (case-insensitive)
                    text_lower = text_stripped.lower()
                    if any(keyword in text_lower for keyword in cls._error_keywords):
                        # This is an error - log it IMMEDIATELY to error.jsonl
                        try:
                            # Ensure error logger is initialized
                            from ..utils.error_logger import SafeErrorLogger

                            if not SafeErrorLogger._initialized:
                                SafeErrorLogger._initialize()

                            # Use synchronous, immediate logging
                            log_error_message(
                                f"Stderr error captured: {text_stripped}",
                                level="ERROR",
                                component="StderrInterceptor",
                                context={
                                    "source": "stderr",
                                    "original_output": text_stripped[:200],
                                },
                            )

                            # CRITICAL: Force immediate flush to ensure it's written to
                            # disk
                            if (
                                SafeErrorLogger._error_file
                                and SafeErrorLogger._error_file != sys.stderr
                            ):
                                try:
                                    SafeErrorLogger._error_file.flush()
                                    import os

                                    os.fsync(
                                        SafeErrorLogger._error_file.fileno()
                                    )  # Force OS-level flush
                                except Exception:
                                    pass  # Flush failed, but error was logged
                        except Exception as e:
                            # If error logging fails, at least print a warning
                            try:
                                if cls._original_stderr is not None:
                                    cls._original_stderr.write(
                                        f"[WARNING] Failed to log stderr error to error.jsonl: {e}\n"
                                    )
                                    cls._original_stderr.flush()
                            except Exception:
                                pass  # Complete failure

            def flush(self) -> None:
                self.original.flush()

            def __getattr__(self, name):
                # Forward all other attributes to original stderr
                return getattr(self.original, name)

        sys.stderr = InterceptingStderr(cls._original_stderr)

    @classmethod
    def stop_intercepting(cls) -> None:
        """Stop intercepting stderr output."""
        if not cls._intercepting or cls._original_stderr is None:
            return

        sys.stderr = cls._original_stderr
        cls._intercepting = False

    @classmethod
    def is_intercepting(cls) -> bool:
        """Check if currently intercepting."""
        return cls._intercepting


def start_stderr_interception() -> None:
    """Public helper to explicitly enable stderr interception."""
    StderrInterceptor.start_intercepting()


def stop_stderr_interception() -> None:
    """Public helper to explicitly disable stderr interception."""
    StderrInterceptor.stop_intercepting()
