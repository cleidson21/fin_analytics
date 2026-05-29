import csv
import re
from pathlib import Path

from models.core import CanonicalTransaction
from taxonomy.categories import Natureza, Perfil
from utils.semantic import normalize_description


OWNERS = ["CLEIDSON RAMOS", "C RAMOS", "CLEIDSON R", "CLEIDSON RAMOS DE CARVALHO"]


def _classification_payload(
    macro: str,
    sub: str,
    natureza: Natureza,
    perfil: Perfil,
) -> dict[str, object]:
    return {
        "macro": macro,
        "sub": sub,
        "macro_categoria": macro,
        "subnatureza": sub,
        "natureza": natureza,
        "perfil": perfil,
    }


def aplicar_regras_semanticas(descricao: str, valor: float) -> dict[str, object] | None:
    desc_upper = normalize_description(descricao).upper()

    is_owner = any(owner in desc_upper for owner in OWNERS)
    if is_owner and any(keyword in desc_upper for keyword in ["TRANSFER", "PIX", "TED"]):
        return _classification_payload(
            "TRANSFERENCIA_INTERNA",
            "INTERNAL_TRANSFER",
            Natureza.TRANSFER,
            Perfil.PATRIMONIAL,
        )

    if valor > 0:
        if any(keyword in desc_upper for keyword in ["SALARIO", "ORDEM BANCARIA", "PAGAMENTO"]):
            return _classification_payload(
                "SALARIO",
                "SALARY",
                Natureza.INCOME,
                Perfil.ESSENCIAL,
            )

        if any(keyword in desc_upper for keyword in ["DIVIDENDO", "RENDIMENTO", "JUROS"]):
            return _classification_payload(
                "DIVIDENDOS",
                "DIVIDEND",
                Natureza.DIVIDEND,
                Perfil.PATRIMONIAL,
            )

        if any(keyword in desc_upper for keyword in ["PIX", "TED", "TRANSFERENCIA RECEBIDA"]):
            return _classification_payload(
                "RECEBIMENTO_DIRETO",
                "PIX_TED_IN",
                Natureza.INCOME,
                Perfil.DISCRICIONARIO,
            )

    if valor < 0 and any(keyword in desc_upper for keyword in ["PIX", "TED", "TRANSFER"]):
        return _classification_payload(
            "PAGAMENTO_DIRETO",
            "PIX_TED_OUT",
            Natureza.EXPENSE,
            Perfil.DISCRICIONARIO,
        )

    return None


class SmartCategorizer:
    def __init__(self, rules_path: Path):
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, path: Path) -> list[dict[str, str]]:
        rules: list[dict[str, str]] = []
        if path.exists():
            with open(path, mode="r", encoding="utf-8") as file_handle:
                reader = csv.DictReader(file_handle)
                for row in reader:
                    if row.get("keyword"):
                        rules.append(row)
        return rules

    def classify(self, transaction: CanonicalTransaction) -> dict[str, object]:
        descricao = transaction.get("descricao_normalizada") or transaction.get("descricao_original") or ""
        descricao = normalize_description(descricao)
        valor = transaction.get("valor", 0)

        semantica = aplicar_regras_semanticas(descricao, valor)
        if semantica:
            return semantica

        for rule in self.rules:
            if re.search(rule["keyword"], descricao, re.IGNORECASE):
                return _classification_payload(
                    rule["macro"],
                    rule["sub"],
                    Natureza(rule["natureza"]),
                    Perfil(rule["perfil"]),
                )

        return _classification_payload(
            "OUTROS",
            "INDEFINIDO",
            Natureza.EXPENSE,
            Perfil.DISCRICIONARIO,
        )