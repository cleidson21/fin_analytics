import hashlib
import logging
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


def normalize_text(value: str) -> str:
    """Remove acentos e espaços extras."""
    if not value:
        return ""

    normalized = unicodedata.normalize("NFKD", str(value))
    clean = "".join([c for c in normalized if not unicodedata.combining(c)])
    return clean.strip().upper()


def parse_br_date(date_str: str) -> date | None:
    """Converte 'dd/mm/yyyy' para objeto date nativo."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        logger.warning(f"Data inválida ignorada: '{date_str}'")
        return None


def parse_currency(value: str | None) -> Decimal | None:
    if value is None:
        return None

    raw = str(value).strip()

    if raw in {"", "-"}:
        return Decimal("0.00")

    raw = raw.replace("R$", "").replace("$", "").replace("%", "").strip()
    is_negative = False

    if raw.startswith("(") and raw.endswith(")"):
        is_negative = True
        raw = raw[1:-1].strip()

    if raw.startswith("-"):
        is_negative = True
        raw = raw[1:].strip()

    raw = raw.replace(" ", "")

    decimal_separator = None
    if "," in raw and "." in raw:
        decimal_separator = "," if raw.rfind(",") > raw.rfind(".") else "."
    elif "," in raw:
        decimal_separator = "," if re.search(r",\d{1,2}$", raw) else None
    elif "." in raw:
        decimal_separator = "." if re.search(r"\.\d{1,2}$", raw) else None

    try:
        if decimal_separator == ",":
            normalized = raw.replace(".", "").replace(",", ".")
        elif decimal_separator == ".":
            normalized = raw.replace(",", "")
        else:
            normalized = raw.replace(".", "").replace(",", "")

        value_decimal = Decimal(normalized)
        return -value_decimal if is_negative and value_decimal != 0 else value_decimal

    except InvalidOperation:
        return None


def parse_br_currency(value: str | None) -> Decimal | None:
    """Mantém compatibilidade com o nome antigo usado pelos parsers."""
    return parse_currency(value)


def generate_economic_id(*args) -> str:
    """Gera um SHA-256 determinístico baseado nos campos semânticos."""
    raw_string = "|".join(str(a).strip() for a in args).encode("utf-8")
    return hashlib.sha256(raw_string).hexdigest()