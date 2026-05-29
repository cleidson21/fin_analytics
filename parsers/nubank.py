import csv
import logging
from pathlib import Path

from models.core import CanonicalTransaction, Source
from utils.semantic import normalize_description
from utils.transformers import generate_economic_id, parse_br_currency, parse_br_date

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"Data", "Valor", "Identificador", "Descrição"}


def parse_nubank_file(file_path: Path) -> list[CanonicalTransaction]:
    """Lê um CSV do Nubank e converte para o modelo CanonicalTransaction."""
    transactions: list[CanonicalTransaction] = []

    with open(file_path, mode="r", encoding="utf-8-sig") as file_handle:
        sample = file_handle.read(2048)
        file_handle.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(file_handle, dialect=dialect)

        fieldnames = set(reader.fieldnames or [])
        if not REQUIRED_COLUMNS.issubset(fieldnames):
            logger.error(f"Arquivo ignorado {file_path.name}: faltam colunas obrigatorias.")
            return []

        for row_num, row in enumerate(reader, start=2):
            dt_str = row.get("Data", "").strip()
            valor_str = row.get("Valor", "0").strip()
            desc_str = row.get("Descrição", "")
            identificador = row.get("Identificador", "").strip()

            dt_obj = parse_br_date(dt_str)
            valor_dec = parse_br_currency(valor_str)

            if not dt_obj or valor_dec is None:
                logger.warning(f"[{file_path.name}:{row_num}] Dados invalidos (Data ou Valor). Ignorando.")
                continue

            desc_norm = normalize_description(desc_str)
            id_economico = generate_economic_id(Source.NUBANK, dt_obj, valor_dec, desc_norm, identificador)

            transactions.append(
                {
                    "id_economico": id_economico,
                    "source": Source.NUBANK,
                    "data": dt_obj,
                    "descricao_original": desc_str,
                    "descricao_normalizada": desc_norm,
                    "valor": valor_dec,
                    "identificador_externo": identificador,
                }
            )

    logger.info(f"Sucesso: {file_path.name} ({len(transactions)} transações)")
    return transactions


def parse_all_nubank(data_dir: Path) -> list[CanonicalTransaction]:
    """Lê todos os CSVs na pasta raw/nubank/."""
    all_transactions: list[CanonicalTransaction] = []
    nubank_dir = data_dir / "raw" / "nubank"

    if not nubank_dir.exists():
        logger.warning(f"Diretório não encontrado: {nubank_dir}")
        return []

    for file_path in nubank_dir.glob("*.csv"):
        all_transactions.extend(parse_nubank_file(file_path))

    return all_transactions
