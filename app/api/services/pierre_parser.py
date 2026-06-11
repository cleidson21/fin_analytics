from __future__ import annotations

import csv
import logging
import re
import unicodedata
from io import StringIO
from datetime import datetime
from decimal import Decimal, InvalidOperation

from models.core import Source
from utils.semantic import normalize_description
from utils.transformers import generate_economic_id, parse_br_currency, parse_br_date


logger = logging.getLogger(__name__)


DATE_AMOUNT_RE = re.compile(
    r"(?P<date>\d{2}/\d{2}/\d{4})\s*(?P<sign>[+-]?)\s*R\$\s*(?P<amount>[\d\.]+,\d{2})(?P<tail>.*)$"
)

HEADER_HINTS = ("DESCRI", "CATEGORI", "CONTADATAVALOR", "CONTA", "VALOR")
ACCOUNT_HINTS = ("Nubank",)
EMOJI_ONLY_RE = re.compile(r"^[\W_]+$", re.UNICODE)

CATEGORY_HINTS = {
    "Transferências",
    "Transferência - PIX",
    "Transferência - Mesma instituição",
    "Transferência mesma titularidade",
    "Investimentos",
    "Serviços",
    "Serviços digitais",
    "Compras",
    "Compras online",
    "Restaurantes, bares e lanchonetes",
    "Postos de gasolina",
    "Farmácia",
    "Telecomunicação",
    "Entre contas",
    "Lazer",
    "Supermercado",
    "Manutenção de veículos",
    "Hospitais, clínicas e laboratórios",
    "Celular",
    "Seguros",
    "Vestiário",
    "Ética",
    "Alimentos e bebidas",
    "Transporte",
    "Eletricidade",
    "Streaming de música",
    "Pagamento de cartão de crédito",
}

CSV_COLUMNS = ("n°", "Data", "Descrição", "Categoria", "Conta", "Valor")


def _strip_diacritics(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _strip_emojis(value: str) -> str:
    return re.sub(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]", " ", value)


def _normalize_line(value: str) -> str:
    text = value.replace("\ufeff", " ").replace("\xa0", " ")
    text = _strip_emojis(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _sniff_dialect(raw_text: str) -> csv.Dialect:
    sample = raw_text[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,")
    except csv.Error:
        return csv.excel


def _get_value(row: dict[str, str], *aliases: str) -> str:
    for alias in aliases:
        if alias in row and row[alias] is not None:
            return str(row[alias]).strip()
    return ""


def _is_header_line(value: str) -> bool:
    compact = _strip_diacritics(value).upper().replace(" ", "")
    return any(hint in compact for hint in HEADER_HINTS)


def _is_category_or_account_line(value: str) -> bool:
    compact = _normalize_line(value)
    if not compact:
        return False

    if any(account_hint in compact for account_hint in ACCOUNT_HINTS):
        return True

    return compact in CATEGORY_HINTS or any(compact.startswith(category) for category in CATEGORY_HINTS)


def _parse_amount(value: str, sign: str = "") -> Decimal | None:
    raw = value.replace(".", "").replace(",", ".").strip()
    if not raw:
        return None

    try:
        amount = Decimal(raw)
    except InvalidOperation:
        return None

    if sign == "-":
        amount = -amount

    return amount


def _infer_category(description: str, fallback: str = "") -> str:
    source_text = f"{description} {fallback}".lower()

    mapping = (
        ("uber", "Táxi e transporte privado urbano"),
        ("pix", "Transferência - PIX"),
        ("rdb", "Investimentos"),
        ("google", "Serviços digitais"),
        ("spotify", "Streaming de música"),
        ("posto", "Postos de gasolina"),
        ("farm", "Farmácia"),
        ("mercado", "Compras online"),
        ("shopee", "Compras online"),
        ("amazon", "Compras online"),
        ("pagamento de pix", "Transferência - PIX"),
        ("transferência enviada", "Transferências"),
        ("transferência recebida", "Transferências"),
        ("compra no débito", "Compras"),
        ("resgate rdb", "Investimentos"),
        ("aplicação rdb", "Investimentos"),
        ("eletric", "Eletricidade"),
        ("celular", "Celular"),
        ("lazer", "Lazer"),
        ("seguro", "Seguros"),
    )

    for needle, inferred in mapping:
        if needle in source_text:
            return inferred

    return fallback or "PENDING"


class PierreParser:
    def parse(self, raw_text: str) -> list[dict[str, object]]:
        normalized_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        dialect = _sniff_dialect(normalized_text)
        reader = csv.DictReader(StringIO(normalized_text), dialect=dialect)

        parsed_items: list[dict[str, object]] = []

        for line_index, row in enumerate(reader, start=1):
            date_text = _get_value(row, "Data")
            description = _get_value(row, "Descrição", "Descricao")
            category = _get_value(row, "Categoria")
            account = _get_value(row, "Conta")
            amount_text = _get_value(row, "Valor")

            source_line_no = line_index

            parsed_date = parse_br_date(date_text)
            amount_value = parse_br_currency(amount_text)

            if parsed_date is None or amount_value is None or not description:
                logger.warning("Linha Pierre ignorada: data, descrição ou valor inválidos.")
                continue

            description_clean = re.sub(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]", "", description)
            description_clean = re.sub(r"\s+", " ", description_clean).strip()
            description_normalized = normalize_description(description_clean)
            source_value = account.upper() if account else "PIERRE"

            amount_normalized = amount_value.quantize(Decimal("0.01"))

            parsed_items.append(
                {
                    "id_economico": generate_economic_id(
                        "MANUAL",
                        "PIERRE",
                        source_line_no,
                        parsed_date.isoformat(),
                        description_normalized,
                        str(amount_normalized),
                        source_value,
                    ),
                    "source": source_value,
                    "origin": "PIERRE",
                    "domain": "FINANCE",
                    "source_line_no": source_line_no,
                    "data": parsed_date,
                    "date": parsed_date.isoformat(),
                    "descricao_original": description_clean,
                    "descricao_normalizada": description_normalized,
                    "description": description_clean,
                    "categoria_origem": category,
                    "valor": amount_value,
                    "amount": amount_value,
                    "identificador_externo": None,
                    "account": account,
                    "category_inferred": _infer_category(description_clean, category),
                    "status": "PENDING",
                }
            )

        return parsed_items