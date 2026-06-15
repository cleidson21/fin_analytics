"""etl/normalizers/__init__.py — Registry de normalizers disponíveis."""
from etl.normalizers.nubank_conta import NubankContaNormalizer
from etl.normalizers.nubank_fatura import NubankFaturaNormalizer
from etl.normalizers.myprofit import MyProfitNormalizer
from etl.normalizers.pierre import PierreNormalizer

# Ordem importa: normalizers mais específicos primeiro
REGISTRY: list = [
    NubankFaturaNormalizer(),   # fatura antes de conta (colunas diferentes)
    NubankContaNormalizer(),
    MyProfitNormalizer(),
    PierreNormalizer(),
]

__all__ = [
    "REGISTRY",
    "NubankContaNormalizer",
    "NubankFaturaNormalizer",
    "MyProfitNormalizer",
    "PierreNormalizer",
]
