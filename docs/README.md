> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela.

<<<<<<< HEAD
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
=======
# Índice da Documentação — FIN Analytics

---

## 🏗️ Arquitetura e Fundação

| # | Documento | Conteúdo |
|---|---|---|
| 00 | [00_PRINCIPLES.md](00_PRINCIPLES.md) | Regras gerais do projeto |
| 01 | [01_ARCHITECTURE.md](01_ARCHITECTURE.md) | Visão geral DDD |
| 10 | [10_DECISIONS.md](10_DECISIONS.md) | Log de decisões |
| 46 | [46_INFRASTRUCTURE.md](46_INFRASTRUCTURE.md) | Estrutura de pastas + responsabilidades das camadas |
| — | [decisions/](decisions/) | ADRs formais |

---

## 🏛️ Domínio Canônico ← Leia ANTES de implementar

| # | Documento | Conteúdo |
|---|---|---|
| 29 | [29_DOMAIN_ENTITIES.md](29_DOMAIN_ENTITIES.md) | 12 entidades com todos os campos, tipos e regras |
| 30 | [30_VALUE_OBJECTS.md](30_VALUE_OBJECTS.md) | Money, Ticker, Percentage, DateRange, etc. |
| 31 | [31_ENUMS.md](31_ENUMS.md) | Todos os enums: TransactionType, AssetType, etc. |
| 33 | [33_DOMAIN_RULES.md](33_DOMAIN_RULES.md) | Regras de negócio, identidade, imutabilidade |
| 36 | [36_SOURCE_OF_TRUTH.md](36_SOURCE_OF_TRUTH.md) | Source of Truth por dado + estratégia de sync |

---

## ⚙️ Camada de Aplicação (Application Layer)

| # | Documento | Conteúdo |
|---|---|---|
| 37 | [37_USE_CASES.md](37_USE_CASES.md) | 20 Use Cases com entradas, saídas e pré/pós-condições |
| 38 | [38_COMMANDS.md](38_COMMANDS.md) | 13 Commands com campos e validações |
| 39 | [39_QUERIES.md](39_QUERIES.md) | 11 Queries com filtros e paginação |
| 40 | [40_DTOS.md](40_DTOS.md) | 30+ DTOs (Request, Response, Internal) |
| 41 | [41_PORTS.md](41_PORTS.md) | 19 Ports (Repository, Provider, Infrastructure) |
| 42 | [42_EVENTS.md](42_EVENTS.md) | 12 Eventos de Domínio |
| 43 | [43_APPLICATION_FLOWS.md](43_APPLICATION_FLOWS.md) | Fluxos: Login, Sync Pierre, MyProfit, CSV, IA, Dashboard |
| 44 | [44_DEPENDENCY_MATRIX.md](44_DEPENDENCY_MATRIX.md) | Matriz UC × Repository × Provider × Eventos |
| 45 | [45_ERROR_HANDLING.md](45_ERROR_HANDLING.md) | Hierarquia de erros + fronteiras transacionais |

---

## 🔌 Providers e Mapeamento

| # | Documento | Conteúdo |
|---|---|---|
| 11 | [11_INTEGRATIONS.md](11_INTEGRATIONS.md) | Arquitetura de integrações Pierre e MyProfit |
| 16 | [16_PIERRE_REFERENCE.md](16_PIERRE_REFERENCE.md) | Referência técnica Pierre Finance |
| 17 | [17_MYPROFIT_REFERENCE.md](17_MYPROFIT_REFERENCE.md) | Referência técnica MyProfit |
| 20 | [20_REST_ENDPOINTS.md](20_REST_ENDPOINTS.md) | 24 endpoints REST Pierre (extraídos do OpenAPI) |
| 21 | [21_PROVIDER_MODELS.md](21_PROVIDER_MODELS.md) | 27 Schemas do OpenAPI Pierre |
| 23 | [23_MCP_TOOLS.md](23_MCP_TOOLS.md) | 11 ferramentas MCP Pierre |
| 32 | [32_PROVIDER_MAPPING.md](32_PROVIDER_MAPPING.md) | Mapeamento Pierre/MyProfit/CSV/YFinance → Canônico |

---

## 🏗️ Infrastructure

| # | Documento | Conteúdo |
|---|---|---|
| 47 | [47_DATABASE_LAYER.md](47_DATABASE_LAYER.md) | SQLAlchemy, Alembic, UoW, índices |
| 48 | [48_SECURITY.md](48_SECURITY.md) | JWT, bcrypt, secrets, CORS, rate limit |
| 49 | [49_CONFIGURATION.md](49_CONFIGURATION.md) | Todas as variáveis de ambiente |
| 50 | [50_LOGGING.md](50_LOGGING.md) | Logging estruturado, auditoria, o que nunca logar |
| 52 | [52_DEPLOYMENT.md](52_DEPLOYMENT.md) | Docker, migrations, health check, backup |

---

## 📋 Implementação

| # | Documento | Conteúdo |
|---|---|---|
| 51 | [51_TESTING.md](51_TESTING.md) | Estratégia de testes: unit, integration, E2E |
| 53 | [53_CODING_STANDARDS.md](53_CODING_STANDARDS.md) | Padrões: nomenclatura, imports, typing, regras absolutas |
| 54 | [54_IMPLEMENTATION_ORDER.md](54_IMPLEMENTATION_ORDER.md) | Sequência oficial: Fase 2 → 11 |
| 55 | [55_DEFINITION_OF_DONE.md](55_DEFINITION_OF_DONE.md) | Checklist obrigatório de conclusão |

---

## 📡 Referência do Ambiente

| # | Documento | Conteúdo |
|---|---|---|
| 19 | [19_ENVIRONMENT.md](19_ENVIRONMENT.md) | Guia de variáveis e carregamento |
| 25 | [25_ERROR_CODES.md](25_ERROR_CODES.md) | Códigos de erro Pierre |
| 26 | [26_PAGINATION.md](26_PAGINATION.md) | Paginação Pierre |
| 27 | [27_RATE_LIMITS.md](27_RATE_LIMITS.md) | Rate limits Pierre |
| 28 | [28_WEBHOOKS.md](28_WEBHOOKS.md) | Webhooks: NÃO existem na Pierre |

---

## 📜 ADRs (Architecture Decision Records)

| ADR | Conteúdo |
|---|---|
| [decisions/](decisions/) | ADR-001 a ADR-010 + futuros |
| ADR-009 | Pierre não possui dados de investimentos — MyProfit assume responsabilidade |
| ADR-010 | Sistema Single User com Bootstrap Automático (Fim do Multi-User) |

---

## ⚠️ Documentos Consolidados (não precisam ser lidos independentemente)

| Doc Antigo | Substituído por |
|---|---|
| `02_DOMAIN_MODEL.md` | `29_DOMAIN_ENTITIES.md` |
| `12_CANONICAL_MODEL.md` | `29_DOMAIN_ENTITIES.md` + `32_PROVIDER_MAPPING.md` |
| `14_PROVIDER_LIFECYCLE.md` | `36_SOURCE_OF_TRUTH.md` + `43_APPLICATION_FLOWS.md` |
| `15_PROVIDER_DISCOVERY.md` | `16_PIERRE_REFERENCE.md` + `17_MYPROFIT_REFERENCE.md` |
| `18_PROVIDER_COMPARISON.md` | `32_PROVIDER_MAPPING.md` |
| `22_OPEN_FINANCE.md` | `20_REST_ENDPOINTS.md` + `32_PROVIDER_MAPPING.md` |
| `24_JSON_SCHEMAS.md` | `21_PROVIDER_MODELS.md` |
>>>>>>> 021d439dcbb06040c0005dbd27456a26c9f1d7e9
