# backend/domains/pierre/__init__.py
# Domínio Pierre — Fonte oficial das movimentações financeiras.
# Responsabilidades deste domínio:
#   - Sincronizar contas e transações da API Pierre
#   - Persistir dados via UPSERT idempotente (PK: provider + external_id)
#   - Manter catálogo de categorias (sync automático)
#   - Registrar governança de sync (sync_state, sync_history)
#
# Limites:
#   - NÃO recalcula nem interpreta dados — persiste exatamente o que recebe
#   - NÃO expõe tabelas internas a outros domínios (comunicação via service público)
#   - NÃO cria colunas preventivas ou campos não documentados
