import csv
import re
from pathlib import Path

from models.core import CanonicalTransaction
from taxonomy.categories import Natureza, Perfil
from utils.semantic import normalize_description


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

        for rule in self.rules:
            if re.search(rule["keyword"], descricao, re.IGNORECASE):
                return {
                    "macro": rule["macro"],
                    "sub": rule["sub"],
                    "natureza": Natureza(rule["natureza"]),
                    "perfil": Perfil(rule["perfil"]),
                }

        return {
            "macro": "OUTROS",
            "sub": "INDEFINIDO",
            "natureza": Natureza.EXPENSE,
            "perfil": Perfil.DISCRICIONARIO,
        }