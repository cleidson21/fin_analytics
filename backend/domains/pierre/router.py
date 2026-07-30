"""
router.py — Domínio Pierre

Endpoints FastAPI do domínio Pierre.
Endpoints previstos:
  POST /pierre/sync          → dispara sincronização (modo PROD ou DEV)
  POST /pierre/sync/replay   → replay de JSON salvo (modo REPLAY)
  GET  /pierre/accounts      → lista contas sincronizadas
  GET  /pierre/transactions  → lista transações sincronizadas
  GET  /pierre/sync/status   → estado atual da sincronização (sync_state)
  GET  /pierre/sync/history  → histórico de execuções (sync_history)

Regras:
  - Nenhum endpoint consome a API Pierre diretamente
  - Toda resposta vem exclusivamente do banco local
  - Nenhum dado mockado
"""

from fastapi import APIRouter

router = APIRouter(prefix="/pierre", tags=["pierre"])

# TODO Sprint 4.4.2 — implementar endpoints
