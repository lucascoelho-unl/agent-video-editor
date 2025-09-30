"""Centralized logging configuration for the agent worker."""

import logging
import os
import sys

log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

# Use basicConfig with force=True to override any existing logger configuration.
# This ensures our logging format is applied consistently across the application.
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True,
)


def get_logger(name: str) -> logging.Logger:
    """Retrieivs a logger instance, which will inherit the root logger's configuration."""
    return logging.getLogger(name)
