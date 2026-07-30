"""
router.py — Domínio Dashboard

Endpoints FastAPI de visualização consolidada.
Endpoints previstos:
  GET /dashboard/overview       → visão geral (saldo, gastos, patrimônio)
  GET /dashboard/cashflow       → fluxo de caixa Pierre (Sprint 4.4.4)
  GET /dashboard/portfolio      → patrimônio MyProfit (Sprint 4.5)
  GET /dashboard/consolidated   → cruzamento Pierre × MyProfit (Sprint 4.6)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# TODO Sprint 4.4.4 — implementar endpoints
