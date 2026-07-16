from __future__ import annotations

import logging
import sys


_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def setup_logging() -> None:
    """Configure the project root logger for console output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    has_console_handler = any(
        isinstance(handler, logging.StreamHandler) and getattr(handler, "stream", None) is sys.stdout
        for handler in root_logger.handlers
    )
    if has_console_handler:
        return

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a named application logger."""
    return logging.getLogger(name)
