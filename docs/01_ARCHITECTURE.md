> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.
> Em caso de conflito entre documentos, `60_ARCHITECTURE_REVISION_V31.md` prevalece.

# 01 — Arquitetura do FINANALYTICS V3

**Versão:** 3.0 | **Status:** VIGENTE | **Data:** 2026-07-30

---

## Visão Geral

O FINANALYTICS é um sistema de gestão financeira pessoal que centraliza dados de dois providers externos — **Pierre** (movimentações financeiras) e **MyProfit** (investimentos) — em um banco local, permitindo dashboards, análises consolidadas e insights via IA.

O backend **não interpreta nem recalcula dados dos Providers**. Ele sincroniza, persiste e apresenta.

---

## Filosofia: Pipeline Direto

```
Pierre / MyProfit
        │
        ▼
  Sistema sincroniza
        │
        ▼
  Sistema persiste (banco local)
        │
        ▼
  Sistema consulta
        │
        ▼
  Sistema relaciona
        │
        ▼
  Sistema apresenta
        │
        ▼
  Gemini analisa (Sprint 4.7 — Read Only)
```

Pierre e MyProfit são domínios **independentes**. Só serão cruzados analiticamente na Sprint 4.6.

---

## Organização Física

```
backend/
    domains/
        pierre/    ← movimentações financeiras (contas, transações, categorias)
        myprofit/  ← patrimônio e investimentos (ativos, posições, dividendos)
        dashboard/ ← visões analíticas agregadas
        ai/        ← Gemini (estritamente read only)
        auth/      ← autenticação JWT (single-user)
        shared/    ← infra pura (db, config, security)
```

Cada domínio contém sua própria cadeia vertical: `models`, `schemas`, `repository`, `service`, `router`, `tests`.

---

## Princípios Arquiteturais

Ver `60_ARCHITECTURE_REVISION_V31.md` — Seção 3 (Regras de Ouro).

---

## Referência Completa

Ver [`60_ARCHITECTURE_REVISION_V31.md`](60_ARCHITECTURE_REVISION_V31.md) para todos os detalhes, princípios, modelagem do banco, pipeline e roadmap vigente.
