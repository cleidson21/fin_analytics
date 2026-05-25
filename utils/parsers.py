"""CSV and financial parsing helpers used by ingestion pipelines."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
import re
import unicodedata

_CURRENCY_CLEANUP_PATTERN = re.compile(r"[^0-9,.-]+")
_MULTIPLE_DOTS_PATTERN = re.compile(r"\.(?=.*\.)")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def _strip_accents(value: str) -> str:
	"""Return a stable ASCII-friendly representation for CSV headers."""

	decomposed = unicodedata.normalize("NFKD", value)
	return "".join(character for character in decomposed if unicodedata.category(character) != "Mn")


def normalize_csv_header(value: str) -> str:
	"""Canonicalize a CSV header for comparison and mapping."""

	text = _strip_accents(str(value)).strip().lower()
	text = _WHITESPACE_PATTERN.sub(" ", text)
	text = text.replace("%", " percentual ")
	text = text.replace("/", " ")
	text = text.replace("-", " ")
	text = text.replace(".", " ")
	return _WHITESPACE_PATTERN.sub(" ", text).strip()


def clean_csv_cell(value: Any) -> str:
	"""Normalize noisy CSV cell payloads before numeric parsing."""

	if value is None:
		return ""

	text = str(value).strip()
	if not text:
		return ""

	text = text.replace("\xa0", " ")
	text = _WHITESPACE_PATTERN.sub(" ", text)
	return text.strip()


def parse_br_currency(value: str | Any) -> Decimal:
	"""Parse Brazilian currency-like values into ``Decimal``.

	The parser removes currency markers, thousand separators, percentage signs,
	and other noisy characters before applying a deterministic ``Decimal`` cast.
	Malformed or empty values fall back to ``Decimal("0.00")``.
	"""

	text = clean_csv_cell(value)
	if not text:
		return Decimal("0.00")

	text = _strip_accents(text)
	text = text.replace("R$", "")
	text = text.replace("%", "")
	text = text.replace(" ", "")
	text = text.replace("\t", "")
	text = text.replace("\n", "")
	text = text.replace("\r", "")
	text = text.replace("(", "-").replace(")", "")
	text = _CURRENCY_CLEANUP_PATTERN.sub("", text)

	if not text:
		return Decimal("0.00")

	negative = text.startswith("-")
	if negative:
		text = text[1:]

	if "," in text:
		text = text.replace(".", "")
		text = text.replace(",", ".")
	else:
		text = _MULTIPLE_DOTS_PATTERN.sub("", text)

	if not text or text in {".", ","}:
		return Decimal("0.00")

	if negative:
		text = f"-{text}"

	try:
		return Decimal(text)
	except (InvalidOperation, ValueError, TypeError):
		return Decimal("0.00")
