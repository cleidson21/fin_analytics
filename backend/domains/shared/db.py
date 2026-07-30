"""
db.py — Shared Infrastructure

Engine e SessionFactory SQLAlchemy.
Este módulo é o único ponto de criação de conexão com o banco.
Todos os domínios obtêm sua sessão através deste módulo.

Não contém regras de negócio — apenas infraestrutura de conexão.
"""

# TODO Sprint 4.4.1 — migrar engine/session de database/ para este módulo
