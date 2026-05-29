from decimal import Decimal
from pathlib import Path

from services.categorizer import SmartCategorizer


def testar_taxonomia():
    categorizer = SmartCategorizer(Path("taxonomy/rules.csv"))

    exemplo = {
        "descricao_original": "IFOOD *BURGER KING",
        "descricao_normalizada": "IFOOD BURGER KING",
        "valor": Decimal("-50.00"),
    }

    classificacao = categorizer.classify(exemplo)
    print("TESTE DE TAXONOMIA")
    print(f"  {exemplo['descricao_normalizada']} -> {classificacao}")
    print()


if __name__ == "__main__":
    testar_taxonomia()