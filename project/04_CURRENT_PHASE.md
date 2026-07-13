# FINANALYTICS V3 — CURRENT PHASE
> Documento pequeno e sempre atual. Atualizado ao início e fim de cada fase.
> **Leia este arquivo primeiro ao retomar o projeto em uma nova conversa.**

---

## ⚡ FASE ATUAL: 3 — Ledger Core (Banking + Dashboard)

**Status:** 🔄 Em andamento
**Iniciada em:** 2026-06-25
**Objetivo:** Implementar o domínio de Banking, provendo repositórios, rotas e engines de DTOs para Transações e Dashboard Financeiro base.
## ⚡ MACROFASE ATUAL: Plataforma de Investimentos

A Plataforma de Ingestão (Fase 5 base) encontra-se **✅ CERTIFICADA E CONSOLIDADA**. O ciclo contínuo de auditorias da fundação foi encerrado na EA6.

### Objetivo Principal da Plataforma de Investimentos
Estruturar e unificar a ingestão de custódia, negociação e proventos (Renda Variável e Fixa) mantendo total compatibilidade com a infraestrutura e governança (Event Sourcing) criadas na fase anterior.

### Domínios da Arquitetura de Investimentos
- **Custódia**: Posição estática (ex: Área do Investidor B3, Snapshots). Requer abstração não-transacional.
- **Movimentações**: Trades, Compras/Vendas via Notas de Corretagem (Event Sourcing integral).
- **Proventos**: Rendimentos já tratados parcialmente, com necessidade de consolidação de calendários.
- **Carteiras**: Agrupamento lógico para cálculo de rentabilidade (MyProfit, CEI).
- **Reconciliação**: Cruzamento do financeiro da conta com a liquidação na B3.

### Roadmap Oficial (Sprints de Investimento)
- [x] TSK-INV-1A: [Sprint 1A] Arquitetura B3 (Zero parser, apenas DTOs e Domínio Isolado).
- [x] TSK-INV-1A.5: [Sprint 1A.5] Levantamento Técnico da B3 (Especificação Oficial).
- [x] TSK-INV-1B: [Sprint 1B] Reader B3 Custódia.
- [x] TSK-INV-1C: [Sprint 1C] Parser B3 Custódia.
- [x] TSK-INV-1D: [Sprint 1D] Normalizer B3 Custódia.
- [x] TSK-INV-1E: [Sprint 1E] Pipeline B3 Custódia.
- [x] TSK-INV-2: [Sprint 2] Persistência B3 e Valuation.
- [x] TSK-INV-3A: [Sprint 3A] CEI (Levantamento e Arquitetura).
- [x] TSK-INV-3B: [Sprint 3B] CEI (Homologação).
- [x] TSK-INV-3C.1: [Sprint 3C.1] CEI (Homologação Funcional).
- [x] TSK-INV-3C.2: [Sprint 3C.2] CEI (Implementação) - Gate 6.5 (Idempotência Financeira TD-02) Concluído.
- [x] TSK-INV-4.0: [Sprint 4] Open Finance Investimentos - Gate 7.0 (Auditoria de Entrada) Concluído.
- [x] TSK-INV-4.1: [Sprint 4] Open Finance Investimentos - Gate 7.1 (Migration 005) Concluído.
- [x] TSK-INV-4.2: [Sprint 4] Open Finance Investimentos - Gate 7.2 (SnapshotRepository) Concluído.
- [x] TSK-INV-4.3: [Sprint 4] Open Finance Investimentos - Gate 7.3 (Adapters) Concluído.
- [x] TSK-INV-4.4: [Sprint 4] Open Finance Investimentos - Gate 7.4 (Orquestração CLI/API) Concluído.
- [x] TSK-INV-5.0: [Sprint 5] Position Engine - Gate 8.1 (Motor de Consolidação Patrimonial) Concluído.
- [x] TSK-INV-5.1: [Sprint 5] Position Engine - Gate 8.2 (Valuation Engine MTM) Concluído.
- [x] TSK-INV-5.2: [Sprint 5] Position Engine - Gate 8.3 (Wealth Engine Global) Concluído.
- [x] TSK-INV-5.3: [Sprint 5] Performance Engine - Gate 8.4 (MWR, TWR, CAGR, YoC) Concluído.
- [x] TSK-INV-6.0: [Sprint 6] Dashboard Analítico - Gate 9.0 (Auditoria de Adaptação do Frontend) Concluído.
- [x] TSK-INV-6.1: [Sprint 6] Dashboard Analítico - Gate 9.1 (Investments Router) Concluído.
- [x] TSK-INV-6.2: [Sprint 6] Dashboard Analítico - Gate 9.2 (Hooks de Integração) Concluído.
- [x] TSK-INV-6.3: [Sprint 6] Dashboard Analítico - Gate 9.3 (Integração de Banco) Concluído.
- [x] TSK-INV-6.4: [Sprint 6] Dashboard Analítico - Gate 9.4 (Nova Tela de Posições MTM) Concluído.
- [x] TSK-INV-6.5: [Sprint 6] Dashboard Analítico - Gate 9.5 (Nova Tela de Performance) Concluído.
- [x] TSK-INV-6.6: [Sprint 6] Dashboard Analítico - Gate 9.6 (Tela de Ingestão e Conciliação) Concluído.
- [x] TSK-INV-6.7: [Sprint 6] Dashboard Analítico - Gate 9.7 (Conciliação) Concluído.

---

## 3. Próxima Sprint (Sprint 7)
Foco primário: Governança, Testes de Integração e Dívidas Técnicas remanescentes, refinamento do Core do Motor de Performance em séries temporais.
- [x] TSK-INV-7.1: [Sprint 7] Gate 10.1 - Pipeline Real de Importação (CSV, OFX, JSON) Concluído.
- [x] TSK-INV-7.2: [Sprint 7] Gate 10.2 - Ledger de Importações e Auditoria Permanente Concluído.

> Consulte o `project/09_IMPLEMENTATION_QUEUE.md` para o status detalhado da microetapa atual.

---

## O que vem após esta fase

### FASE 3 — Ledger Core (Banking + Dashboard)
Com a ingestão estruturada e as carteiras importadas, será iniciada a construção das APIs do Ledger.
