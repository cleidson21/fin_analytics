"""
config.py — Shared Infrastructure

Settings da aplicação via pydantic-settings.
Lê variáveis de .env e fornece configurações tipadas para todos os domínios.

Configurações previstas:
  - DATABASE_URL
  - PIERRE_API_KEY / PIERRE_API_URL
  - MYPROFIT_API_KEY / MYPROFIT_API_URL
  - JWT_SECRET / JWT_ALGORITHM / JWT_EXPIRE_MINUTES
  - ENV (development | production)
  - DEBUG_SAVE_RAW_JSON (bool — modo DEV)
"""

# TODO Sprint 4.4.1 — migrar Settings de core/config.py para este módulo
