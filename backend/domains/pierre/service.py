"""
service.py — Domínio Pierre

Orquestração das regras de negócio e fluxo de sincronização.
Responsável por:
  - Coordenar pipeline.py → repository.py
  - Controlar modos de operação: PROD | DEV | REPLAY
  - Garantir que sync_state e sync_history sejam atualizados após cada execução
  - Expor interface pública para o domínio dashboard consumir (via schemas)

Interface pública (para comunicação inter-domínios):
  - get_accounts_summary() → AccountsSummarySchema
  - get_transactions_summary() → TransactionsSummarySchema

Regras:
  - Nunca acessa tabelas de outros domínios diretamente
  - Nunca escreve de volta na API Pierre
"""

# TODO Sprint 4.4.2 — implementar service
