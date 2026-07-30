"""
router.py — Domínio Auth

Endpoints FastAPI de autenticação.
Endpoints previstos:
  POST /auth/login    → retorna JWT
  POST /auth/refresh  → renova token
  GET  /auth/me       → dados do usuário autenticado
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

# TODO Sprint 4.4.1 — implementar endpoints de auth
