"""
utils/logger.py — Centralised logging configuration for InterviewGuard backend.

Usage anywhere in the app:
    from app.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("something happened")

Log format:
    2024-01-15 14:32:01  INFO     app.routes.session   Session STARTED id=abc123
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# ── Config ────────────────────────────────────────────────────────────────────

LOG_LEVEL   = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_TO_FILE = os.environ.get("LOG_TO_FILE", "true").lower() == "true"

_BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR     = os.path.join(_BASE_DIR, "data")
LOG_FILE    = os.path.join(LOG_DIR, "interviewguard.log")

_FMT        = "%(asctime)s  %(levelname)-8s %(name)-30s %(message)s"
_DATE_FMT   = "%Y-%m-%d %H:%M:%S"

# ── Internal state — configure only once ─────────────────────────────────────

_configured = False


def _configure():
    global _configured
    if _configured:
        return
    _configured = True

    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    # Console handler — always on
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    # Rotating file handler — 5 MB × 3 backups
    if LOG_TO_FILE:
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes    = 5 * 1024 * 1024,   # 5 MB
                backupCount = 3,
                encoding    = "utf-8",
            )
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError as e:
            root.warning("Could not create log file %s: %s", LOG_FILE, e)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# ── Public API ────────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger, configuring the root handler on first call.

    Example
    -------
    logger = get_logger(__name__)
    logger.info("Session started: %s", session_id)
    """
    _configure()
    return logging.getLogger(name)