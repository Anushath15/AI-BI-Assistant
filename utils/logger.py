"""
utils/logger.py

Centralized logging configuration for AI BI Assistant.

All modules should import logger from here rather than
calling logging.getLogger(__name__) independently.
This gives us a single place to control log format,
level, and output destination.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger for the given module name.

    Usage in any module:
        from utils.logger import get_logger
        logger = get_logger(__name__)

    Parameters
    ----------
    name  : Module name, typically __name__
    level : Optional override for log level

    Returns
    -------
    logging.Logger
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    logger.setLevel(level or logging.INFO)
    return logger


# Root logger for the application
root_logger = get_logger("ai_bi_assistant")