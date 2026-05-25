"""Text normalization helpers used across the ingestion pipeline.

These utilities are intentionally framework-agnostic so they can be reused in
ETL, domain rules, and tests without introducing extra dependencies.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
import unicodedata

_NON_ALNUM_PATTERN = re.compile(r"[^0-9A-Z]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_text(value: str) -> str:
	"""Return a stable, uppercase, accent-free representation of text.

	The normalization rules are:
	- trim leading and trailing whitespace,
	- decompose Unicode characters and remove combining marks,
	- convert to uppercase,
	- replace non-alphanumeric characters with spaces,
	- collapse consecutive whitespace into a single space.

	Args:
		value: Raw input text.

	Returns:
		A normalized string suitable for deterministic comparisons.
	"""

	decomposed = unicodedata.normalize("NFKD", value.strip())
	without_accents = "".join(
		character
		for character in decomposed
		if unicodedata.category(character) != "Mn"
	)
	uppercased = without_accents.upper()
	replaced = _NON_ALNUM_PATTERN.sub(" ", uppercased)
	return _WHITESPACE_PATTERN.sub(" ", replaced).strip()


def parse_brazilian_currency(val: str | None) -> Decimal | None:
	"""Parse a Brazilian currency string into ``Decimal``.

	Empty values return ``None``. Malformed non-empty values raise ``ValueError``.
	"""

	if val is None:
		return None

	text = str(val).strip()
	if not text:
		return None

	text = text.replace("R$", "").replace("\xa0", " ").replace(" ", "")
	if "," in text:
		text = text.replace(".", "").replace(",", ".")

	text = re.sub(r"[^0-9.\-]", "", text)
	if text in {"", "-", ".", "-."}:
		return None

	try:
		return Decimal(text)
	except InvalidOperation as exc:
		raise ValueError(f"Unable to parse Brazilian currency value: {val!r}") from exc


def parse_brazilian_percentage(val: str | None) -> Decimal | None:
	"""Parse a Brazilian percentage string into ``Decimal``.

	Empty values return ``None``. Malformed non-empty values raise ``ValueError``.
	"""

	if val is None:
		return None

	text = str(val).strip()
	if not text:
		return None

	text = text.replace("%", "").replace("\xa0", " ").replace(" ", "")
	if "," in text:
		text = text.replace(".", "").replace(",", ".")

	text = re.sub(r"[^0-9.\-]", "", text)
	if text in {"", "-", ".", "-."}:
		return None

	try:
		return Decimal(text)
	except InvalidOperation as exc:
		raise ValueError(f"Unable to parse Brazilian percentage value: {val!r}") from exc
