# backend/domains/myprofit/__init__.py
# Domínio MyProfit — Fonte oficial dos investimentos e patrimônio.
# Responsabilidades deste domínio:
#   - Sincronizar ativos, posições, dividendos e rentabilidade do MyProfit
#   - Persistir dados via UPSERT idempotente
#   - Manter histórico de patrimônio
#
# Limites:
#   - Domínio paralelo e INDEPENDENTE do domínio Pierre
#   - NÃO insere transações no domínio financeiro (Pierre)
#   - NÃO recalcula nem interpreta dados
#   - Comunicação com outros domínios: apenas via service público + schemas
