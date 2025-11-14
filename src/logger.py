"""Logging utilities for the expense tracker project."""

from __future__ import annotations

import logging
import os
from functools import lru_cache


@lru_cache(maxsize=None)
def get_logger(name: str = "expense_tracker") -> logging.Logger:
    """Return a configured logger instance.

    The log level defaults to INFO but can be overridden with the
    LOG_LEVEL environment variable.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger




