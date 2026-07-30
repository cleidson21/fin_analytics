# backend/domains/pierre/tests/__init__.py
# Testes isolados do domínio Pierre.
# Cobertura obrigatória (Sprint 4.4.5 — Definition of Done):
#   - test_sync_idempotence.py  → Replay: 2 execuções = 0 duplicações
#   - test_pipeline_modes.py   → PROD / DEV / REPLAY funcionam corretamente
#   - test_upsert.py           → accounts e transactions sem duplicação
#   - test_governance.py       → sync_state e sync_history preenchidos corretamente
