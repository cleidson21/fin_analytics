"""
router.py — Domínio MyProfit

Endpoints FastAPI do domínio MyProfit (Sprint 4.5).
Endpoints previstos:
  POST /myprofit/sync        → dispara sincronização
  GET  /myprofit/assets      → lista ativos
  GET  /myprofit/positions   → posições/custódia
  GET  /myprofit/dividends   → histórico de dividendos
  GET  /myprofit/portfolio   → visão de patrimônio
"""

from fastapi import APIRouter

router = APIRouter(prefix="/myprofit", tags=["myprofit"])

# TODO Sprint 4.5 — implementar endpoints
