> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela.

# Índice da Documentação — FINANALYTICS V3

**Versão:** 3.0 | **Data:** 2026-07-30

---

## 🚨 Referência Principal da Arquitetura V3

> [!IMPORTANT]
> Em caso de conflito entre qualquer documento abaixo e o arquivo `60_ARCHITECTURE_REVISION_V31.md`, **o 60 prevalece sempre**.

| # | Documento | Conteúdo |
|---|---|---|
| 60 | [60_ARCHITECTURE_REVISION_V31.md](60_ARCHITECTURE_REVISION_V31.md) | **⭐ REFERÊNCIA ARQUITETURAL OFICIAL V3** — Princípios, schema canônico, pipeline, estrutura de domínios, roadmap |
| 61 | [61_SPRINT_4_4_DOD.md](61_SPRINT_4_4_DOD.md) | **Definition of Done — Sprint 4.4** (checklist executável) |

---

## 🏗️ Arquitetura e Fundação (Atualizado para V3)

| # | Documento | Status V3 | Conteúdo |
|---|---|---|---|
| 00 | [00_PRINCIPLES.md](00_PRINCIPLES.md) | ✅ Válido | Regras gerais do projeto |
| 01 | [01_ARCHITECTURE.md](01_ARCHITECTURE.md) | ✅ Atualizado | Visão geral V3, Vertical Slices, pipeline direto |
| 02 | [02_DOMAIN_MODEL.md](02_DOMAIN_MODEL.md) | ✅ Atualizado | 5 domínios V3, isolamento, source of truth |
| 03 | [03_DATABASE.md](03_DATABASE.md) | ✅ Atualizado | Schema canônico V3 (accounts, transactions, categories, sync_state, sync_history) |
| 05 | [05_IMPORT_PIPELINE.md](05_IMPORT_PIPELINE.md) | ✅ Atualizado | Pipeline direto: PROD / DEV / REPLAY |
| 09 | [09_ROADMAP.md](09_ROADMAP.md) | ✅ Atualizado | Sprints 4.4 → 4.7 |
| 10 | [10_DECISIONS.md](10_DECISIONS.md) | ✅ Válido | Log de decisões |
| 19 | [19_ENVIRONMENT.md](19_ENVIRONMENT.md) | ✅ Válido | Configuração de ambiente |

---

## 🔌 Referência dos Providers

| # | Documento | Status V3 | Conteúdo |
|---|---|---|---|
| 16 | [16_PIERRE_REFERENCE.md](16_PIERRE_REFERENCE.md) | ✅ Válido | Referência da API Pierre (contratos, payloads reais) |
| 17 | [17_MYPROFIT_REFERENCE.md](17_MYPROFIT_REFERENCE.md) | ✅ Válido | Referência da API MyProfit |

---

## 📦 Documentos Legados (Pré-V3)

> [!WARNING]
> Os documentos abaixo foram escritos para a arquitetura anterior (camadas horizontais / DDD clássico). Estão **preservados como histórico**, mas não representam a arquitetura vigente. Não devem ser usados como referência de implementação.

| # | Documento | Observação |
|---|---|---|
| 29 | [29_DOMAIN_ENTITIES.md](29_DOMAIN_ENTITIES.md) | Obsoleto — entidades redefinidas no schema V3 |
| 32 | [32_PROVIDER_MAPPING.md](32_PROVIDER_MAPPING.md) | Obsoleto — mapeamento eliminado no V3 |
| 40 | [40_DTOS.md](40_DTOS.md) | Obsoleto — DTOs agora em `schemas.py` por domínio |
| 37 | [37_USE_CASES.md](37_USE_CASES.md) | Referência histórica — Use Cases revisados no V3 |
| 38 | [38_COMMANDS.md](38_COMMANDS.md) | Referência histórica |
| 39 | [39_QUERIES.md](39_QUERIES.md) | Referência histórica |
| 41 | [41_PORTS.md](41_PORTS.md) | Obsoleto — Ports substituídos por services públicos entre domínios |
| 46 | [46_INFRASTRUCTURE.md](46_INFRASTRUCTURE.md) | Obsoleto — estrutura de camadas substituída por Vertical Slices |
| 54 | [54_IMPLEMENTATION_ORDER.md](54_IMPLEMENTATION_ORDER.md) | Obsoleto — substituído pelo Roadmap de Sprints 4.4–4.7 |
| 20 | [20_REST_ENDPOINTS.md](20_REST_ENDPOINTS.md) | Referência parcial — endpoints V3 definidos por domínio em `router.py` |

---

## 🛡️ Documentos Complementares (Ainda Válidos)

| # | Documento | Conteúdo |
|---|---|---|
| 25 | [25_ERROR_CODES.md](25_ERROR_CODES.md) | Códigos de erro padronizados |
| 48 | [48_SECURITY.md](48_SECURITY.md) | Política de segurança e JWT |
| 50 | [50_LOGGING.md](50_LOGGING.md) | Estratégia de logs |
| 51 | [51_TESTING.md](51_TESTING.md) | Estratégia de testes (adaptar para Vertical Slices) |
| 52 | [52_DEPLOYMENT.md](52_DEPLOYMENT.md) | Configuração de deploy |
| 53 | [53_CODING_STANDARDS.md](53_CODING_STANDARDS.md) | Padrões de código |
| — | [decisions/](decisions/) | ADRs formais |
