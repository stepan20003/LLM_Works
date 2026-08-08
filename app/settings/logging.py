"""Centralized structured logging configuration using Rich."""

import logging
from rich.logging import RichHandler
from app.settings.settings import settings


def setup_logging() -> None:
    """Configure root logger with Rich formatting for beautiful terminal outputs."""
    log_level = logging.DEBUG if settings.debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )

    # Silence noisy third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)