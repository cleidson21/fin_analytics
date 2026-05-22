"""Runtime settings for fin_analytics.

This module separates runtime configuration from immutable business constants.
Values are read from environment variables or from a local `.env` file.

Use :func:`get_settings` to obtain the cached settings instance.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR: Path = REPO_ROOT / "data"
DEFAULT_DATABASE_DIR: Path = DEFAULT_DATA_DIR / "database"
DEFAULT_DATABASE_PATH: Path = DEFAULT_DATABASE_DIR / "fin_analytics.duckdb"
DEFAULT_LOGS_DIR: Path = REPO_ROOT / "logs"
ENV_FILE: Path = REPO_ROOT / ".env"


def _resolve_path(value: object, default: Path) -> Path:
	"""Resolve a path-like value into an absolute :class:`~pathlib.Path`.

	Args:
		value: Raw value received from the environment.
		default: Fallback path used when the value is empty or missing.

	Returns:
		An absolute path with user-home expansion applied.
	"""

	if value is None:
		return default

	if isinstance(value, str) and not value.strip():
		return default

	return Path(str(value)).expanduser().resolve()


class Settings(BaseSettings):
	"""Application settings loaded from environment variables.

	The model uses Pydantic v2 and keeps all filesystem locations as
	:class:`pathlib.Path` instances.
	"""

	model_config = SettingsConfigDict(
		env_file=ENV_FILE,
		env_file_encoding="utf-8",
		case_sensitive=False,
		extra="ignore",
	)

	APP_ENV: Literal["development", "staging", "production"] = Field(
		default="development",
		description="Execution environment.",
	)
	APP_LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
		default="INFO",
		description="Minimum log level emitted by the application.",
	)
	APP_TIMEZONE: str = Field(
		default="UTC",
		description="Default IANA timezone used by the application.",
	)

	DATA_DIR: Path = Field(
		default=DEFAULT_DATA_DIR,
		description="Root directory for all data artifacts.",
	)
	RAW_DIR: Path = Field(
		default=DEFAULT_DATA_DIR / "raw",
		description="Directory for raw source files.",
	)
	STAGING_DIR: Path = Field(
		default=DEFAULT_DATA_DIR / "staging",
		description="Directory for intermediate normalized files.",
	)
	PROCESSED_DIR: Path = Field(
		default=DEFAULT_DATA_DIR / "processed",
		description="Directory for curated and validated files.",
	)
	DATABASE_DIR: Path = Field(
		default=DEFAULT_DATABASE_DIR,
		description="Directory that stores the local DuckDB file.",
	)
	DATABASE_PATH: Path = Field(
		default=DEFAULT_DATABASE_PATH,
		description="Full path to the local DuckDB database file.",
	)
	LOGS_DIR: Path = Field(
		default=DEFAULT_LOGS_DIR,
		description="Directory for application log files.",
	)

	DATABASE_READ_ONLY: bool = Field(
		default=False,
		description="Open DuckDB in read-only mode.",
	)
	DATABASE_THREADS: int = Field(
		default=4,
		ge=0,
		description="Number of CPU threads used by DuckDB.",
	)
	DATABASE_MEMORY_LIMIT: str = Field(
		default="1GB",
		description="Maximum RAM available to DuckDB.",
		pattern=r"^\d+(\.\d+)?\s*(KB|MB|GB|TB)$",
	)

	NUBANK_CSV_ENCODING: str = Field(
		default="utf-8",
		description="Character encoding used by Nubank CSV exports.",
	)
	NUBANK_DATE_FORMAT: str = Field(
		default="%d/%m/%Y",
		description="Date format used by Nubank CSV exports.",
	)
	MYPROFIT_CSV_ENCODING: str = Field(
		default="utf-8",
		description="Character encoding used by MyProfit CSV exports.",
	)
	MYPROFIT_DATE_FORMAT: str = Field(
		default="%Y-%m-%d",
		description="Date format used by MyProfit CSV exports.",
	)

	@model_validator(mode="before")
	@classmethod
	def _normalize_input(cls, data: object) -> object:
		"""Normalize path-like inputs before Pydantic validates the model.

		Args:
			data: Raw settings payload.

		Returns:
			The normalized payload.
		"""

		if not isinstance(data, dict):
			return data

		path_fields = (
			"DATA_DIR",
			"RAW_DIR",
			"STAGING_DIR",
			"PROCESSED_DIR",
			"DATABASE_DIR",
			"DATABASE_PATH",
			"LOGS_DIR",
		)

		normalized = dict(data)
		for field_name in path_fields:
			if field_name not in normalized:
				continue

			raw_value = normalized[field_name]
			if raw_value is None or (isinstance(raw_value, str) and not raw_value.strip()):
				normalized.pop(field_name)
				continue

			normalized[field_name] = Path(str(raw_value)).expanduser().resolve()

		return normalized

	@model_validator(mode="after")
	def _derive_default_paths(self) -> "Settings":
		"""Rebuild derived directories when only ``DATA_DIR`` changes.

		Returns:
			The validated settings instance.
		"""

		provided_fields = self.__pydantic_fields_set__

		if "DATA_DIR" not in provided_fields:
			self.DATA_DIR = DEFAULT_DATA_DIR

		if "RAW_DIR" not in provided_fields:
			self.RAW_DIR = self.DATA_DIR / "raw"

		if "STAGING_DIR" not in provided_fields:
			self.STAGING_DIR = self.DATA_DIR / "staging"

		if "PROCESSED_DIR" not in provided_fields:
			self.PROCESSED_DIR = self.DATA_DIR / "processed"

		if "DATABASE_DIR" not in provided_fields:
			self.DATABASE_DIR = self.DATA_DIR / "database"

		if "DATABASE_PATH" not in provided_fields:
			self.DATABASE_PATH = self.DATABASE_DIR / "fin_analytics.duckdb"

		if "LOGS_DIR" not in provided_fields:
			self.LOGS_DIR = DEFAULT_LOGS_DIR

		return self

	def ensure_directories(self) -> None:
		"""Create the configured directories if they do not exist."""

		for directory in (
			self.DATA_DIR,
			self.RAW_DIR,
			self.STAGING_DIR,
			self.PROCESSED_DIR,
			self.DATABASE_DIR,
			self.LOGS_DIR,
			self.DATABASE_PATH.parent,
		):
			directory.mkdir(parents=True, exist_ok=True)

	@property
	def database_uri(self) -> str:
		"""Return the DuckDB file path as a string."""

		return str(self.DATABASE_PATH)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	"""Load settings once per process.

	Returns:
		A cached :class:`Settings` instance.
	"""

	load_dotenv(dotenv_path=ENV_FILE, override=False)
	return Settings()
