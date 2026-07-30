> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.
> Em caso de conflito entre documentos, `60_ARCHITECTURE_REVISION_V31.md` prevalece.

# 02 — Modelo de Domínios V3

**Versão:** 3.0 | **Status:** VIGENTE | **Data:** 2026-07-30

---

## Domínios do Sistema

O FINANALYTICS V3 é organizado em **5 domínios verticais** + infraestrutura compartilhada:

| Domínio | Pasta | Responsabilidade | Sprint |
|---------|-------|-----------------|--------|
| **pierre** | `domains/pierre/` | Contas, transações, categorias, governança de sync | 4.4 |
| **myprofit** | `domains/myprofit/` | Ativos, posições, dividendos, patrimônio | 4.5 |
| **dashboard** | `domains/dashboard/` | Visões analíticas consolidadas | 4.4.4 / 4.5 / 4.6 |
| **ai** | `domains/ai/` | Insights Gemini (Read Only) | 4.7 |
| **auth** | `domains/auth/` | Autenticação JWT, bootstrap admin | 4.4.1 |
| **shared** | `domains/shared/` | Engine, Session, Settings, JWT helpers | 4.4.1 |

---

## Isolamento e Comunicação

```
┌──────────────┐     ┌─────────────────┐
│   pierre/    │     │   myprofit/     │
│  service.py  │──┐  │   service.py    │──┐
└──────────────┘  │  └─────────────────┘  │
                  ▼                        ▼
           ┌─────────────────────────────────┐
           │         dashboard/service.py    │
           └─────────────────────────────────┘
                          │
                          ▼
                    dashboard/router.py → Frontend
```

**Regras de isolamento:**
- Nenhum domínio acessa as tabelas internas de outro domínio diretamente
- Comunicação ocorre exclusivamente via **services públicos** usando **schemas como contrato**
- É proibido um `utils.py` global com regras de negócio de múltiplos domínios

---

## Source of Truth

| Dado | Provider Oficial | Tabelas |
|------|-----------------|---------|
| Contas bancárias e cartões | Pierre | `accounts` |
| Transações financeiras | Pierre | `transactions` |
| Categorias de gastos | Pierre | `categories` |
| Ativos e posições B3 | MyProfit | `assets`, `positions` |
| Dividendos | MyProfit | `dividends` |
| Patrimônio | MyProfit | `portfolio_snapshots` |

---

## Referência Completa

Ver [`60_ARCHITECTURE_REVISION_V31.md`](60_ARCHITECTURE_REVISION_V31.md) — Seções 4 (Source of Truth) e 8 (Estrutura Arquitetural).
