> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela.

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
