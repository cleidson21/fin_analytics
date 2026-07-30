"""
models.py — Domínio Pierre

Mapeamento SQLAlchemy das tabelas do domínio Pierre:
  - accounts      (PK: provider + external_id)
  - transactions  (PK: provider + external_id)
  - categories    (PK: provider + name)
  - sync_state    (PK: provider)
  - sync_history  (PK: id autoincrement)

Regras de ouro:
  - Nenhuma coluna preventiva (Schema First — aprovação antes de adicionar)
  - extra_json existe apenas para campos desconhecidos; nunca será lido como lógica
  - Toda alteração estrutural ocorre EXCLUSIVAMENTE por Migration versionada
"""

# TODO Sprint 4.4.1 — implementar models SQLAlchemy
