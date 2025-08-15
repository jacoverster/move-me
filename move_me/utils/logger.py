"""Logging configuration for Move Me."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO", log_file: Optional[Path] = None
) -> logging.Logger:
    """Set up logging configuration."""

    # Convert string level to logging level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    level = level_map.get(log_level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger("move_me")
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the Move Me logger."""
    return logging.getLogger("move_me")
