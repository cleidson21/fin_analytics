<<<<<<< HEAD
> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.
> Em caso de conflito entre documentos, `60_ARCHITECTURE_REVISION_V31.md` prevalece.
=======

> [!IMPORTANT]
> A pasta docs/ é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela. Toda nova implementação deve ler os documentos existentes em docs/, atualizá-los quando necessário e registrar decisões arquiteturais por meio de ADRs antes de prosseguir.

# Roadmap
>>>>>>> 021d439dcbb06040c0005dbd27456a26c9f1d7e9

# 09 — Roadmap V3

**Versão:** 3.0 | **Status:** VIGENTE | **Data:** 2026-07-30

---

## Sequência de Entregas

### Sprint 4.4 — Pierre Completo (Prioridade Máxima)

| Sub-entrega | Conteúdo | Status |
|-------------|----------|--------|
| **4.4.1** | Banco e Pipeline base: models SQLAlchemy, migrations Alembic, pipeline skeleton, shared/ infra | 🔲 Pendente |
| **4.4.2** | Sincronização Pierre: UPSERT real de accounts e transactions, modos PROD/DEV/REPLAY | 🔲 Pendente |
| **4.4.3** | Governança: alimentação de `sync_state` e `sync_history`, tela de status no frontend | 🔲 Pendente |
| **4.4.4** | Dashboard com dados reais: zero mocks, consumo exclusivo do banco local | 🔲 Pendente |
| **4.4.5** | Teste de Replay: idempotência comprovada (2 execuções = 0 duplicações) | 🔲 Pendente |

### Sprint 4.5 — MyProfit
Sincronização de Carteira, Ativos, Dividendos. Dashboard de patrimônio.

### Sprint 4.6 — Relacionamento
Cruzamento analítico Pierre × MyProfit. Visão consolidada de fluxo de caixa × patrimônio.

### Sprint 4.7 — Gemini (Read Only)
Análises e insights via LLM sobre dados estabilizados. Sem escrita no banco.

---

## Fora do Escopo V1.0 (Congelado)

- Importação via CSV ou OFX
- Open Finance genérico (Banco Central)
- Novos Providers além de Pierre e MyProfit
- Reclassificação automática por IA
- Alteração automática de categorias
- Escrita de dados de volta nos Providers
- Colunas preventivas para funcionalidades futuras

---

## Definition of Done — Sprint 4.4

Ver [`61_SPRINT_4_4_DOD.md`](61_SPRINT_4_4_DOD.md) para o checklist completo e executável.

---

## Referência Completa

Ver [`60_ARCHITECTURE_REVISION_V31.md`](60_ARCHITECTURE_REVISION_V31.md) — Seção 9 (Roadmap V3.1).
