"""
repository.py — Domínio Pierre

Camada de acesso exclusivo ao banco para as tabelas do domínio Pierre.
Responsável por:
  - UPSERT idempotente de accounts (ON CONFLICT: provider, external_id → UPDATE)
  - UPSERT idempotente de transactions (ON CONFLICT: provider, external_id → UPDATE)
  - INSERT OR IGNORE de categories (catálogo — nunca sobrescreve)
  - UPDATE de sync_state
  - INSERT de sync_history

Regras:
  - Apenas este repository lê/escreve nas tabelas do domínio Pierre
  - Nenhum outro domínio importa este módulo diretamente
  - Toda query produtora de efeitos deve ser testada com Replay (idempotência)
"""

# TODO Sprint 4.4.1 — implementar repository
