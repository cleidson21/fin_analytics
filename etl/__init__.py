"""
etl/ — Package do pipeline ETL v2 (Sprint 4.4)

Estrutura:
  etl/
    __init__.py          ← este arquivo
    base.py              ← Protocol EventNormalizer
    matcher.py           ← EventMatcher (fingerprint duplo)
    reconciler.py        ← EventReconciler (cruzamento cross-source)
    classifier.py        ← EventClassifier (wraps SmartCategorizer)
    normalizers/
      __init__.py
      nubank_conta.py    ← CSV extrato conta corrente Nubank
      nubank_fatura.py   ← CSV fatura cartão Nubank
      myprofit.py        ← CSVs MyProfit (posições, proventos, evolução)
      pierre.py          ← CSV/TXT Pierre (extrato)
"""
from etl.base import EventNormalizer, build_raw_event, make_semantic_id, make_cross_fingerprint

__all__ = [
    "EventNormalizer",
    "build_raw_event",
    "make_semantic_id",
    "make_cross_fingerprint",
]
