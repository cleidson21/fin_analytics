"""Formatting helpers for the Streamlit user interface.

These utilities keep presentation logic isolated from the service and
repository layers.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def format_currency_br(value: Decimal) -> str:
	"""Format a decimal value as Brazilian currency.

	Args:
		value: Monetary value to format.

	Returns:
		A string in the Brazilian currency format, for example
		``R$ 1.500,50`` or ``-R$ 1.500,50``.
	"""

	quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
	absolute_text = f"{abs(quantized):,.2f}"
	formatted = absolute_text.replace(",", "X").replace(".", ",").replace("X", ".")
	prefix = "-" if quantized < 0 else ""
	return f"{prefix}R$ {formatted}"


def format_percentage(value: Decimal) -> str:
	"""Format a decimal value as a percentage string.

	Args:
		value: Percentage value to format.

	Returns:
		A string formatted with a decimal comma, for example ``15,4%``.
	"""

	quantized = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
	absolute_text = f"{abs(quantized):.1f}".replace(".", ",")
	prefix = "-" if quantized < 0 else ""
	return f"{prefix}{absolute_text}%"
