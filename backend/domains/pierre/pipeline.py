"""
pipeline.py — Domínio Pierre

Lógica central de importação/sincronização.
Implementa o pipeline direto sem lógicas de dedução:

  [PROD]   Pierre API → JSON em memória ──┐
  [DEV]    Pierre API → exports/pierre/raw/ → memória ──┤
  [REPLAY] exports/pierre/raw/<arquivo> → memória ──────┘
                                                        │
                                                        ▼
                                             Validação simples (Pydantic)
                                                        │
                                                        ▼
                                          Accounts UPSERT (provider, external_id)
                                                        │
                                                        ▼
                                        Transactions UPSERT (provider, external_id)
                                                        │
                                                        ▼
                                          Categories INSERT OR IGNORE
                                                        │
                                                        ▼
                                         sync_state UPDATE + sync_history INSERT

Regras do pipeline:
  - Idempotência absoluta: rodar 2x com o mesmo JSON = mesmo resultado
  - Nenhum campo calculado ou deduzido
  - Campos desconhecidos → extra_json (sem falhar)
  - O pipeline NÃO sabe nada sobre frontend ou outros domínios
"""

# TODO Sprint 4.4.2 — implementar pipeline
