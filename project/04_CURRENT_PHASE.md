# FINANALYTICS V3 — CURRENT PHASE
> Documento pequeno e sempre atual. Atualizado ao início e fim de cada fase.
> **Leia este arquivo primeiro ao retomar o projeto em uma nova conversa.**

---

## ⚡ FASE ATUAL: 3 — Ledger Core (Banking + Dashboard)

**Status:** 🔄 Em andamento
**Iniciada em:** 2026-06-25
**Objetivo:** Implementar o domínio de Banking, provendo repositórios, rotas e engines de DTOs para Transações e Dashboard Financeiro base.
## ⚡ FASE ATUAL: 5 — Importadores & Governança

A Fase 4 (Credit & Installments) foi ✅ CERTIFICADA e congelada.

## Objetivo Principal da Fase 5
Estabelecer os pipelines de importação assíncrona/síncrona (Pierre e MyProfit) respeitando as restrições de governança V3 (Auditabilidade e Rollback total através das chaves de `run_id`).

## Tarefas desta fase

- [x] TSK-5.0-1: Construir Catálogo de Fontes de Dados (Data Sources Catalog) e Matrizes de Reconciliação.
- [x] TSK-5.1-0: Modelagem da Camada de Importação, Matrizes de Precedência, Duplicidade e Conflitos.
- [x] TSK-5.1-00: Reorganização Documental e Desmembramento da Fase 5 (10 Subsistemas).
- [x] TSK-5.1-00B: Matriz Suprema (23), Canonical Event Base (24), e Importers Catalog (25).
- [x] TSK-5.1-1: [Foundation] Implementar entidades ImportRun, ImportBatch, ImportSession e CanonicalFinancialEvent em Python.
- [x] TSK-5.1-1B: [Foundation] Instituir a política de 4 Níveis de Auditoria Visual (Doc 27).
- [x] TSK-5.2-1: [Sprint V1] Nubank Conta (Pipeline Completo: Reader -> Normalizer -> Reconciliation -> Governança -> Banco).
- [x] TSK-5.3-1: [Sprint V2] Nubank Fatura (Pipeline Completo).
- [x] TSK-5.ER: [Enterprise Review] Auditoria arquitetural completa da Fase 5 (Docs 30–33). APROVADA COM RESSALVAS.
- [x] TSK-5.R1: [Refactoring] Refatorações P1 Pós Enterprise Review (BaseCsvReader, Parser Defensivo).
- [x] TSK-5.4-1: [Sprint V3] Pierre TXT (Pipeline Completo).
- [x] TSK-5.R2: [Hardening] REF-010 (parser estrutural) + REF-011 (67 testes Pierre).
- [ ] TSK-5.5-1: [Sprint V4] MyProfit Ativos e Proventos (Pipeline Completo).
- [ ] TSK-5.6-1: [Sprint V5] B3 Custódia (Pipeline Completo).
- [ ] TSK-5.7-1: [Sprint V6] Pierre TXT (Pipeline Completo).
- [ ] TSK-5.8-1: [Sprint V7] Nota de Negociação PDF (OCR + Pipeline Completo).

---

> Consulte o `project/09_IMPLEMENTATION_QUEUE.md` para o status detalhado da microetapa atual.

---

## Próximo Gate

- `GET /transactions` retorna paginação correta, filtrando de acordo com os DTOs documentados no Front.
- Dashboard básico responde métricas (ainda que zeradas ou processadas por mock engine inicial).

---

## O que vem após esta fase

### FASE 3 — Ledger Core (Banking + Dashboard)
**Primeiro passo exato:**
1. Criar `backend/domains/banking` e suas subpastas.
2. Mapear DTOs para `Transaction`.
3. Criar repositório `transactions` com suporte a paginação e filtros.
