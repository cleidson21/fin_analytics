# FINANALYTICS V3 — TECHNICAL DEBT (RC1)
> Inventário final de Dívidas Técnicas controladas na versão Release Candidate.

## 1. Dívidas Técnicas P2 (Menor Gravidade)
*Estas dívidas não quebram o código e foram aprovadas como aceitáveis para a V3.*

- **TD-001 (Imports):** O arquivo de importação do MyProfit de "Ativos" não foi implementado pois sua estrutura não atende o modelo de Eventos Financeiros Canônicos, já que consiste em um snapshot em vez de movimentações. Foi preferido importar apenas "Proventos".
- **TD-002 (Testes):** O pydantic gera um DeprecationWarning nos testes por conta do `datetime.utcnow()` que será descontinuado no Python 3.12+ (Sugestão de migração para `datetime.now(timezone.utc)` para V4).
- **TD-003 (Mocks):** Em alguns testes de Integração e E2E, repositórios em memória não recriam inteiramente falhas exóticas de SQLite (ex: database locked), garantindo validações de regra de negócio, mas sub-testando timeouts de banco sob extremo volume.
- **TD-004 (Subscriptions Proxy):** A tabela `subscriptions` oficial nunca foi implementada. O serviço usa uma heurística lendo as transações normais filtradas por `categories` (ex: `services.streaming`) para gerar a visada de Assinaturas, economizando tabelas à custa de alguma fragilidade na categorização.
- **TD-005 (Módulos de Inicialização):** O `PluginManager` assume que as dependências internas dos plugins não precisam de um Gráfico de Injeção de Dependências profundo (Dependency Injection Framework) pois o número de plugins no V3 é baixo (apenas 4 plugins internos de IA), porém isso não vai escalar se houver 50 plugins na V4.

## 2. Refatorações Aconselhadas para a V4
- Adoção de SQLAlchemy Async (2.0) + `asyncio` e bibliotecas `httpx` assíncronas, substituindo as funções bloqueantes (sync).
- Refatoração dos DTOs trocando o uso indiscriminado de `Field(default_factory)` por tipagens opcionais seguras do Pydantic v2.
- Adoção de um Broker Real (Kafka, RabbitMQ) caso a arquitetura Single User escale para Multi-Tenant, matando o Internal Event Bus na sua forma in-memory.
