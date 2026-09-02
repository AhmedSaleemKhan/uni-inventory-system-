"""
utils/app_logger.py
Central logging configuration. Writes rotating logs to /logs and echoes
warnings+ to console.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

import config


def setup_logging() -> None:
    log_file = config.LOGS_DIR / "uaims.log"

    root_logger = logging.getLogger("uaims")
    if root_logger.handlers:
        return  # already configured

    root_logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(file_formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
