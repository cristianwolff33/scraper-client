from __future__ import annotations

import logging
import sys
from pathlib import Path


def get_logger(
    name: str,
    level: str = "INFO",
    log_dir: Path | None = None,
) -> logging.Logger:
    """
    Returns a named logger with console + optional file handlers.
    Safe to call multiple times — handlers are added only once.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)

        info_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(fmt)
        logger.addHandler(info_handler)

        error_handler = logging.FileHandler(log_dir / "errors.log", encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(fmt)
        logger.addHandler(error_handler)

    logger.propagate = False
    return logger
