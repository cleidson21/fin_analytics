"""Reusable logging helpers for fin_analytics.

This module centralizes logger creation so application code can request a
module-scoped logger without duplicating handler setup.
"""

from __future__ import annotations

import logging
from pathlib import Path


LOGS_DIR: Path = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE: Path = LOGS_DIR / "etl.log"
LOG_FORMAT: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def get_logger(module_name: str) -> logging.Logger:
	"""Return a configured logger for a specific module.

	The logger writes to both stdout and ``logs/etl.log``. Handlers are attached
	only once per logger to avoid duplicate log lines.

	Args:
		module_name: Name of the module requesting the logger.

	Returns:
		A configured :class:`logging.Logger` instance.
	"""

	LOGS_DIR.mkdir(parents=True, exist_ok=True)

	logger = logging.getLogger(module_name)
	logger.setLevel(logging.INFO)
	logger.propagate = False

	if logger.handlers:
		return logger

	formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

	console_handler = logging.StreamHandler()
	console_handler.setLevel(logging.INFO)
	console_handler.setFormatter(formatter)

	file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
	file_handler.setLevel(logging.INFO)
	file_handler.setFormatter(formatter)

	logger.addHandler(console_handler)
	logger.addHandler(file_handler)
	return logger
