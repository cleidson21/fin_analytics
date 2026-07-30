"""
router.py — Domínio AI (Gemini)

Endpoints FastAPI para análises inteligentes via LLM (Sprint 4.7).
Endpoints previstos:
  POST /ai/analyze    → análise contextual dos dados financeiros
  GET  /ai/insights   → insights pré-gerados

RESTRIÇÃO: Todos os endpoints são READ ONLY. Nenhum altera estado do banco.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["ai"])

# TODO Sprint 4.7 — implementar endpoints
