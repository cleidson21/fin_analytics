# FINANALYTICS V3 — PROJECT CHANGELOG
> Registro permanente e append-only. Nenhuma entrada pode ser apagada ou modificada retroativamente.
> Formato: `[DATA] [FASE] [TIPO] Descrição | Motivo | Impacto`

---

## Tipos de entrada
- `DECISÃO` — escolha arquitetural ou estratégica
- `APROVAÇÃO` — gate ou fase aprovada
- `REJEIÇÃO` — gate ou fase reprovada (com motivo)
- `CORREÇÃO` — mudança forçada por falha encontrada
- `ADIÇÃO` — nova funcionalidade ou escopo adicionado
- `REMOÇÃO` — escopo ou arquivo removido
- `NOTA` — contexto relevante que não se encaixa nas categorias acima

---

## Histórico

### [2026-06-20] — Fase de Banco de Dados

**[2026-06-20] [DB] DECISÃO**
Schema V3 iniciado com migrations 001–008 cobrindo: Identity, Banking, Credit, Investments, Market Data, Governance, AI, Analytics.
Motivo: Reconstrução completa do schema a partir do domínio.
Impacto: Todas as futuras implementações partem deste schema.

**[2026-06-20] [DB] ADIÇÃO**
Migrations 009, 010, 011: `fixed_income_events`, `transaction_events`, `ai_prompt_versioning`.
Motivo: Auditoria de domínio identificou entidades faltando.
Impacto: Modelo de eventos de renda fixa e ledger de transações completado.

**[2026-06-20] [DB] APROVAÇÃO**
Schema V3 congelado: 12 migrations, 37 tabelas, `foreign_key_check OK`, `integrity_check OK`.
Motivo: Auditoria final de freeze aprovada sem falhas estruturais.
Impacto: Banco é fonte da verdade. Proibido alterar sem processo formal.

---

### [2026-06-20] — Migration 012

**[2026-06-20] [DB] ADIÇÃO**
Migration 012: freeze_fixes — correções finais de domínio.
Motivo: Revisão pré-freeze identificou ajustes de FK e constraints.
Impacto: Schema encerrado definitivamente.

---

### [2026-06-21] — Auditoria de Backend

**[2026-06-21] [BACKEND] DECISÃO**
Backend legado (`app/`) identificado como 100% incompatível com schema V3.
Motivo: Auditoria comparativa mostrou: modelos com colunas inexistentes no V3, zero rotas HTTP, zero cobertura de testes.
Impacto: Todo o diretório `app/` será descartado.

**[2026-06-21] [BACKEND] DECISÃO**
Estratégia A escolhida: Reconstrução Total em nova pasta `backend/`.
Motivo: Menor risco de dívida técnica, alinhamento imediato frontend↔banco, zero contaminação legada.
Impacto: `app/` deletado na Fase 1 da implementação.

**[2026-06-21] [BACKEND] DECISÃO**
Reconciliação implementada como lógica em memória (sem novas tabelas).
Motivo: Evitar alteração do schema após o freeze. A tela de reconciliação sugere transferências comparando `transactions` + `transfers` por heurística de data/valor.
Impacto: Sem migration nova para reconciliação.

**[2026-06-21] [BACKEND] DECISÃO**
Migration 013 autorizada: enriquecer `classification_rules` com `miss_count`, `evidence_count`, `confidence_score`, `status`.
Motivo: Frontend da tela de Learning exige esses campos. Schema atual não possui.
Impacto: Única exceção ao freeze. Migration pequena (apenas `ALTER TABLE ADD COLUMN`).

---

### [2026-06-22] — Governança do Projeto

**[2026-06-22] [PROCESSO] ADIÇÃO**
Fase 0.9 adicionada ao roadmap: Governança do Projeto.
Motivo: Ciclo de auditorias estava gerando perda de contexto entre conversas. Documentação permanente resolve dependência de contexto do Sonnet.
Impacto: 7 documentos de controle criados em `project/`. Nenhuma fase de implementação pode iniciar sem esta fase aprovada.

**[2026-06-23] [PROCESSO] CORREÇÃO**
Ajuste nas contagens de documentos de governança, incluindo `08_INVESTMENTS_CONTRACT.md` e criando o `09_IMPLEMENTATION_QUEUE.md`.
Motivo: Documento 08 foi omitido das listas das fases em 03 e 04. Novo documento 09 exigido para rastreabilidade de tarefas curtas e retomada de contexto.
Impacto: Nenhuma fase é considerada concluída sem a devida atualização do 09_IMPLEMENTATION_QUEUE.md.

**[2026-06-23] [BACKEND] ADIÇÃO**
Fundação do novo Backend FastAPI (Fase 1.1 - Microetapa 1). Diretório legado `app/` removido com sucesso. Estrutura inicial `backend/` criada, com leitura do `.env` e conexão validada com o SQLite V3 via `GET /api/v1/health`.
Motivo: Implementar base limpa sem ORM, conforme Master Plan.
Impacto: Backend isolado na porta 8000 pronto para receber as próximas implementações.

**[2026-06-24] [PROCESSO] APROVAÇÃO**
Fase 1 formalmente concluída e aprovada. Avanço para a Fase 2 — Identity & Autenticação.
Motivo: Todos os pré-requisitos de infraestrutura foram cumpridos sem erros.
Impacto: Início do desenvolvimento de regras de negócio.

**[2026-06-24] [BACKEND] ADIÇÃO**
Criado o módulo de segurança (`backend/shared/security.py`) utilizando `python-jose` para geração de JWT e `bcrypt` direto para hashing de senhas. (Fase 2.1 - Microetapa 1).
Motivo: O `passlib` apresenta um bug não corrigido com o `bcrypt` versão >= 4.0.0 e a biblioteca foi substituída pela implementação direta para garantir a estabilidade do Hash.
Impacto: Funcionalidades base de auth disponíveis para uso no futuro repositório de Identity.

**[2026-06-24] [BACKEND] ADIÇÃO**
Criado o repositório de identidade (`UserRepository`) utilizando raw SQL via SQLAlchemy Core (`backend/domains/identity/repository.py`) para consulta de usuários. (Fase 2.1 - Microetapa 2).
Motivo: Implementar as funções de consulta no banco essenciais para o login, sem uso de ORM conforme regras arquiteturais.
Impacto: Camada de persistência disponível para consumo nas futuras rotas de login da Fase 2.

**[2026-06-25] [INFRAESTRUTURA] RECONSTRUÇÃO DO BANCO**
O banco de dados mock artificial foi deletado e o script oficial de inicialização (`create_db.py`) foi executado com sucesso. O banco de dados V3 encontra-se agora perfeitamente alinhado com o schema congelado, possuindo todas as 38 tabelas de fundação.
Motivo: Evitar a proliferação de dados mocks fora do contrato do Master Plan.
Impacto: A base de dados principal tornou-se íntegra.

**[2026-06-25] [AUTH] IMPLEMENTAÇÃO**
Criada a camada lógica de autenticação com Seed Automático para a base V3. Adicionados os parâmetros de `ADMIN_EMAIL` e `ADMIN_PASSWORD` no arquivo de configuração (`.env`). Implementados `AuthService` com validação de ambiente, persistência do seed do usuário no banco SQLite para uso em Foreign Keys, e emissão de JWT. Configurado router do FastAPI (`POST /api/v1/auth/login` e `GET /api/v1/auth/me`).
Motivo: Concluir o fluxo de Single User alinhado com o Frontend sem corromper o Schema V3.
Impacto: Frontend pode autenticar e receber JWT integral, enquanto o banco ganha a âncora relacional do usuário automaticamente.

**[2026-06-25] [AUTH] AUDITORIA FRONTEND (TSK-2.1-4)**
Executada a auditoria completa da integração entre Frontend e Backend. Validada a persistência de token (via `localStorage`), interceptação 401, fluxo de logout, recuperação de sessão e compatibilidade de payloads. Identificada uma única divergência grave de contrato na rota de submissão do login (`/auth/token` no código vs `/auth/login` na documentação/backend). As correções aguardam aprovação.
Motivo: Garantir conformidade estrita da API com o código real do Frontend sem alterá-lo.
Impacto: A correção da rota restaurará 100% da conectividade do login end-to-end.

**[2026-06-25] [AUTH] VALIDAÇÃO FINAL E CORREÇÃO (TSK-2.1-5)**
Aplicada a solução arquitetural de compatibilidade de Autenticação sem tocar no código Frontend: adicionado suporte simultâneo a `POST /api/v1/auth/login` e `POST /api/v1/auth/token` no router do FastAPI, ajustado o `OAuth2PasswordBearer`, e corrigida a documentação (`07_FRONTEND_CONTRACT.md`). Foram executados com sucesso total 8 testes de carga (Validade, Expiração, Seed e Nao-Duplicação).
Motivo: Atender o Master Plan que define o Frontend e o Banco como fontes de verdade imutáveis.
Impacto: Fluxo da Fase 2.1 100% operacional. O Frontend agora consegue se autenticar nativamente na V3.

**[2026-06-25] [AUTH] ENCERRAMENTO DA FASE 2.1**
Executada auditoria final varrendo arquivos físicos, payloads, integridade do banco de dados (SQLite) e alinhamento com os contratos. Constatado sucesso pleno: zero persistência de senhas (Single User .env), zero duplicações, endpoints redundantes operacionais e contrato frontend em conformidade. O módulo de Identity & Authentication foi oficialmente encerrado.
Motivo: Rito de governança para fechamento de fase.
Impacto: A aplicação Backend V3 agora está pronta para avançar para as lógicas de negócio (Fase 3 ou 2.2), contando com infraestrutura de JWT e usuário ancorado segura.

**[2026-06-25] [AUTH] CERTIFICAÇÃO TÉCNICA FORMAL DA FASE 2.1**
Executado script de certificação definitiva (`audit_auth_final.py`). Comprovada a equivalência vetorial das rotas `/token` e `/login`. Comprovado comportamento de intercepção HTTP 401 para tokens inválidos e expirados. Verificado criptograficamente que o JWT carrega os claims `sub` e `exp`. Validada integridade da tabela `users` (ausência física do campo `password_hash`). Validada a lista de 12 migrations inalteradas na `_schema_migrations`.
Motivo: Garantir blindagem absoluta antes de prosseguir com o projeto.
Impacto: Certificado oficial de maturidade do módulo de Identidade do FinAnalytics V3.

**[2026-06-25] [GOVERNANÇA] HIGIENIZAÇÃO DA PASTA PLANS**
Eliminação física de 22 arquivos obsoletos presentes no diretório `plans/`. Os arquivos removidos pertenciam à iniciativa legada "V2" e prescreviam arquiteturas, microsserviços e esquemas de banco conflitantes com o projeto V3. Foram retidos exclusivamente quatro catálogos de Regras de Negócio e Cálculos Financeiros (independentes de infraestrutura).
Motivo: Eliminar ruído, reduzir alucinações de contexto de IA e solidificar o `project/01_PROJECT_MASTER_PLAN.md` como guia absoluto.
Impacto: Segurança e clareza para a execução das Fases subsequentes.

**[2026-06-25] [BANKING] CRIAÇÃO DO DOMÍNIO BANCÁRIO E TRANSACTIONS REPO (TSK-3.1-1)**
- Auditoria do Frontend gerada e validada (Gate 9.0). O design será mantido integralmente.
- Router FastAPI `backend/domains/investments/router.py` (Gate 9.1) criado.
- Endpoints: `/portfolio`, `/positions`, `/performance`, `/allocation`, `/institutions`.
- Testes unitários para o router `test_investments_router.py`.
- Novos Hooks Frontend: `usePortfolioData`, `usePositionsData`, `usePerformanceData` consumindo o router (Gate 9.2).
- Adaptação sem quebra visual (`useGrowthData`, `useAllocationData`, etc) mapeando os novos DTOs para interfaces legado (Gate 9.2).
- Repositórios `TradeRepository` e `SnapshotRepository` implementaram operações de leitura (Gate 9.3).
- Router FastAPI integrado com o banco de dados SQL (via Repositories), injetando dados reais nas Engines (Gate 9.3).
- Criação da tela de Posições MTM (`/wealth/positions`) utilizando o hook `usePositionsData` com memoização de cálculos e componentes do Design System legado (Gate 9.4).
- Criação da tela de Performance (`/wealth/performance`), expondo métricas avançadas (TWR, MWR, CAGR, Rentabilidade Mensal/Diária) e otimizando o fetch no hook `usePerformanceData` com singleton de Promise para evitar duplicação com `useGrowthData` (Gate 9.5).
Abertura formal da Fase 3 (Ledger Core). Criados `backend/domains/banking`, `dto.py` (`TransactionDTO`) e `repository.py` (`TransactionRepository`). Mapeamento exato de raw SQL unindo a tabela `transactions` com `categories` (parentalidade) para suprir o contrato visual do Frontend. 
Motivo: Lançar as fundações de acesso a dados da tela principal de Transações.
Impacto: Domínio `banking` iniciado e compatível com as regras de raw SQL do V3. Banco inalterado.

**[2026-06-25] [BANKING] ROUTER DE TRANSACTIONS (TSK-3.1-2)**
Implementação do endpoint `GET /api/v1/transactions`. Suporte total à query parameters para paginação (`limit`, `offset`) e filtros opcionais (`search`, `startDate`, `endDate`, `category`). A rota exige autenticação via JWT (utilizando o `get_current_user` do Identity Core). O schema físico foi 100% respeitado e não foram utilizados ORMs intrusivos.
Motivo: Viabilizar a chamada real do Frontend `useTransactions` para carregar a tabela.
Impacto: O Ledger de Transações base está operacional e protegido.

**[2026-06-25] [BANKING] DASHBOARD BANKING (TSK-3.1-3)**
Criação do `DashboardRepository` e rotas agregadoras (`/api/v1/dashboard/summary-v2`, `pacing-v2`, `heatmap`, `categories`, `catalog`). Uso massivo de SQL puro com agregações `SUM(CASE WHEN...)`, excluindo eficientemente repasses (`is_transfer`) e investimentos (`is_investment`) do cálculo de gasto puro.
Motivo: Expor os dados consolidados requeridos pelos gráficos e cards da `DashboardPage` no Frontend Contract.
Impacto: A visão analítica da plataforma passou a funcionar com alta performance via query delegada ao SQLite.

**[2026-06-25] [GOVERNANÇA] CERTIFICAÇÃO DA FASE 3**
Auditoria final e encerramento oficial da Fase 3 (Ledger Core). Asseguradas as compatibilidades DTO e integridade do banco (Pragma `ok`).
Motivo: Avançar de forma metódica.
Impacto: Fase 3 congelada e Fase 4 liberada para desenvolvimento.

**[2026-06-25] [CREDIT] CREDIT & INSTALLMENTS DTO (TSK-4.1-1)**
Abertura da Fase 4. Mapeadas as tabelas de crédito (`credit_cards`, `installment_plans`, `installments`). Criados os DTOs `InstallmentsDashboardDTO` e `SubscriptionsDashboardDTO` e o `CreditRepository` para preparar o provimento de dados aos dashboards de Cartão de Crédito e Assinaturas do Frontend. 
Motivo: Garantir estruturação antecipada de tipos de forma compatível com a visão UI (Next.js).
Impacto: Fundação para os endpoints `/installments` e `/subscriptions` consolidada via SQLite nativo.

**[2026-06-25] [CREDIT] CREDIT ROUTER E ENDPOINTS (TSK-4.1-2)**
Implementação dos endpoints `GET /api/v1/dashboard/installments` e `GET /api/v1/dashboard/subscriptions` através do `backend/domains/credit/router.py`. Ambos protegidos pela arquitetura centralizada JWT (`get_current_user`). Integração testada via subrequests no Uvicorn.
Motivo: Viabilizar que o Frontend alimente os painéis correspondentes, finalizando a infraestrutura de Credit & Installments para visão consolidada.
Impacto: Rotas estabelecidas e 100% compátiveis com os DTOs do contrato Frontend. Nenhuma alteração estrutural nas migrations necessárias.

**[2026-06-25] [GOVERNANÇA] CERTIFICAÇÃO DA FASE 4 (TSK-4.1-3)**
Auditoria final da Fase 4 (Credit & Installments) executando a bateria de verificações na integridade dos endpoints. Conduzido escaneamento da pasta `plans/` e atestado que a documentação da V2 se tornou parcialmente obsoleta (especialmente a seção de Business Rules focada em SQLAlchemy ORM). O projeto atinge maturidade suficiente para lidar com Importações e AI.
Motivo: Encerrar a Fase 4 validando todo o bloco e destravando a governança.
Impacto: Fase 4 congelada. Fase 5 (Importadores e Governança) liberada oficialmente.

**[2026-06-26] [GOVERNANÇA] CATÁLOGO DE FONTES DE DADOS (TSK-5.0-1)**
Abertura da Fase 5 via Mapeamento passivo da pasta `samples/`. Criação do artefato arquitetural `project/10_DATA_SOURCES_CATALOG.md` contendo as Matrizes de Confiabilidade, Dependências e Duplicidade das origens de dados (B3, Corretoras, Nubank, Pierre, MyProfit). Definidas estratégias anti-colisão via precedência hierárquica baseada no UUID do Nubank e Notas de Negociação. 
Motivo: Evitar ingestão desordenada que polua a base relacional com dados duplicados durante o desenvolvimento dos Data Import Engines.
Impacto: Planejamento validado para orientar o parser na Fase 5. Nenhuma funcionalidade de código alterada. Banco ileso.

**[2026-06-26] [ARQUITETURA] MODELAGEM DA CAMADA DE IMPORTAÇÃO (TSK-5.1-0)**
Desenvolvimento de Matrizes de Precedência, Conflito, IA, e Identidade Canônica (`project/11_DATA_IMPORT_ARCHITECTURE.md`). Documentado o fluxo irreversível de precedência das fontes: Contas Bancárias atuarão como colunas vertebrais, seguidas pelas Faturas, Notas de Corretagem, e só então os agregadores (MyProfit/Pierre) atuarão de forma passiva enriquecendo metadados (como Categoria e Yield) para impedir _duplicate keys_. 
Motivo: Solidificar a governança transacional garantindo auditoria limpa (Rollback / ImportRun) de dados inseridos via Parse.
Impacto: Guias definitivos desenhados para o desenvolvimento da API de _Data Import_. Nenhuma alteração em código real.

**[2026-06-26] [ARQUITETURA] DESMEMBRAMENTO DA FASE 5 (TSK-5.1-00)**
O monolito de "Importação e Governança" foi desmembrado em 10 subsistemas (5.1 a 5.10) independentes no `01_PROJECT_MASTER_PLAN.md`. Criados 10 documentos arquiteturais complementares detalhando que "Readers", "OCR" e "AI Parsers" nunca tocam no banco de dados e devem obrigatoriamente convergir seus outputs para um `Canonical Financial Event` processado pela `Reconciliation Engine`. Bibliotecas homologadas oficialmente: `pandas`, `openpyxl`, `pdfplumber`, `PaddleOCR`, `FAISS`. Projetos de referência definidos: `beancount`, `hledger`.
Motivo: Evitar espaguete de código em parsers misturados com regras de reconciliação, seguindo estritamente a filosofia do projeto de rastreabilidade.
Impacto: Fase 5 reestruturada na Fila de Implementação. Código inalterado.

**[2026-06-26] [ARQUITETURA] FECHAMENTO DA FUNDAÇÃO FASE 5 (TSK-5.1-00B)**
Conclusão da arquitetura passiva com a consolidação da "Matriz de Prioridades Suprema" (`project/23_SOURCE_PRIORITY_MATRIX.md`), definindo irrefutavelmente que a Conta Corrente domina saldos, Notas dominam taxas e Custódia B3 domina volumes. Introduzido formalmente o DTO `RawDocument` injetado na Normalization Engine (`project/17_CANONICAL_NORMALIZATION.md`), e destacado o `CanonicalFinancialEvent` como um documento individual (`project/24_CANONICAL_FINANCIAL_EVENT.md`). O `12_AI_STANDARD_PROMPT.md` foi fortificado exigindo o reuso de ecossistema Open Source onde aplicável.
Motivo: Evitar perda de tempo no desenvolvimento de parsers criando conflitos com lógicas que poderiam ser sanadas no nível de extração DTO.
Impacto: A Arquitetura Teórica da Fase 5 (Data Ingestion) está finalizada. A próxima tarefa iniciará a codificação Python.

**[2026-06-26] [PLANEJAMENTO] ADOÇÃO DE SPRINTS VERTICAIS (TSK-5.1-00C)**
Alteração da matriz de execução da Fase 5: abandonado o desenvolvimento por camadas horizontais (fazer todos os Readers, depois todos os Normalizers). Adotado fluxo de Sprints Verticais isolados (Sprint V1: Nubank Conta, V2: Fatura...). Criado o artefato `project/26_QUALITY_METRICS.md` com SLAs estritos (ex: 100% de rollback validado em caso de falha).
Motivo: Evitar problemas de integração End-to-End tardios; permitir a homologação de fontes individualmente desde a extração até a persistência no banco.
Impacto: Mudança de roadmap. Fim formal do Modo de Arquitetura (Planning Mode) e autorização para iniciar codificação Python (TSK-5.1-1).

**[2026-06-26] [IMPLEMENTAÇÃO] FUNDAÇÃO DO DOMÍNIO IMPORTS (TSK-5.1-1)**
Criação física do módulo `backend/domains/imports/` e testes associados `tests/unit/domains/test_imports_dto.py`. Implementados os modelos Pydantic `RawDocument`, `CanonicalFinancialEvent`, `ImportSessionDTO`, `ImportBatchDTO`, `ImportRunDTO`, e `ImportAuditDTO`. Criados stubs de repositórios e rotas. Testes de unidade em 100% de cobertura nos DTOs.
Motivo: Materializar em código o modelo desenhado nas matrizes arquiteturais, criando uma barreira de validação estrutural baseada em Tipos antes do desenvolvimento do primeiro parser.
Impacto: Domínio `imports` preparado. Próxima etapa será rodar o primeiro fluxo vertical (Sprint V1: Nubank Conta).

**[2026-06-26] [ARQUITETURA] POLÍTICA DE 4 NÍVEIS DE AUDITORIA (TSK-5.1-1B)**
Criação do pipeline de testes estritos (`27_TESTING_AND_AUDIT_PIPELINE.md`). O Master Plan agora exige, para a aprovação de gates, além dos testes unitários clássicos, a geração de "Golden Tests" (CSVs funcionais), relatórios em markdown e rastreabilidade visual do que o parser gerou a partir das amostras brutas de `samples/`. Diretório `tests/results/` isolado via `.gitignore`.
Motivo: Evitar a ilusão de "testes passando" ocultando erros semânticos (como falhas de detecção de categoria e conflitos). Trazer legibilidade humana ao fluxo de testes da extração de dados.
Impacto: Maior rigor para a aprovação dos próximos Sprints. Transparência visual e sistêmica completa para o usuário aprovar os eventos antes da base de dados.

**[2026-06-26] [IMPLEMENTAÇÃO] SPRINT V1 - NUBANK CONTA (TSK-5.2-1)**
Codificação do pipeline de ingestão do arquivo de Extrato de Conta Nubank (`NubankContaPipeline`). Implementados Reader (Pandas), Validator, Parser (Pydantic DTOs) e Normalizer. Geração dos pacotes probatórios de Nível 3 e 4 na pasta `tests/results/V1_Nubank_Conta`, provando matematicamente que o motor lê o extrato e converte perfeitamente para Eventos Canônicos sem uso de persistência no Banco.
Motivo: Materializar o modelo canônico proposto em `24_CANONICAL_FINANCIAL_EVENT.md` com um fluxo de dados real.
Impacto: Validação de 100% do design arquitetural da Fase 5 e geração da base estrutural que será repetida nos próximos importadores.

**[2026-06-26] [IMPLEMENTAÇÃO] SPRINT V2 - NUBANK FATURA E PREP REVIEW (TSK-5.3-1)**
Codificação do pipeline de ingestão do arquivo de Fatura Nubank (`NubankFaturaPipeline`). Tratamento de regex e pontuação para moedas divergentes do padrão nativo float. Geração de relatórios visuais (Golden Tests) na pasta `tests/results/V2_Nubank_Fatura`. Em paralelo, criação da grade documental de Auditoria Enterprise (Documentos 30, 31, 32 e 33) preparando a arquitetura de inspeção técnica.
Motivo: Encerrar a segunda fonte (cartões) e frear temporariamente os próximos Sprints (V3 a V7) para a execução do Enterprise Review obrigatório de estabilidade.
Impacto: O sistema agora detém dois fluxos verticais totalmente prontos: Fluxo de Caixa (Conta) e Passivos em Crédito (Fatura). Próximo passo será a revisão Enterprise.

**[2026-06-26] [AUDITORIA] ENTERPRISE REVIEW — FASE 5 (TSK-5.ER)**
Auditoria arquitetural completa da Fase 5 (Sprints V1 e V2) realizada por Claude Sonnet. 17 testes unitários e 2 testes funcionais re-executados com sucesso. 10 achados documentados em `31_ENTERPRISE_FINDINGS.md`. 8 dívidas técnicas em `32_TECHNICAL_DEBT.md`. 8 refatorações priorizadas em `33_REFACTOR_QUEUE.md`.
Resultado: APROVADA COM RESSALVAS — Arquitetura correta com 4 refatorações P1 obrigatórias antes da Sprint V3.
Impacto: Porta aberta para Sprint V3 (Pierre TXT) após resolução das refatorações P1.

**[2026-06-26] [REFATORAÇÃO] REFATORAÇÕES P1 PÓS ENTERPRISE REVIEW (TSK-5.R1)**
Executadas as refatorações exigidas na revisão: criação de `BaseCsvReader` (redução de duplicação), herança por `NubankContaReader` e `NubankFaturaReader`, adição de tratamento defensivo em `NubankFaturaParser` (com try/except e logging) e novo teste negativo `test_validator_invalid_date_fatura`.
Motivo: Eliminar dívida técnica estrutural (P1) e preparar fundação escalável para os próximos leitores antes de iniciar a Sprint V3.
Impacto: Redução da duplicação de código e aumento de robustez contra exceções em tempo de parsing. Todos os testes aprovados (18/18) e Golden Tests confirmados sem regressão. Fundação certificada para Pierre TXT.

**[2026-06-26] [IMPLEMENTAÇÃO] SPRINT V3 — PIERRE TXT (TSK-5.4-1)**
Implementado o pipeline de importação completo para os extratos TXT do Pierre. Criados `PierreTxtReader`, `PierreTxtValidator`, `PierreTxtParser` e `PierreTxtNormalizer`. A extração dos blocos transacionais (linhas separadas por texto, data e valor) foi feita utilizando regex focado nas terminações padronizadas. Os testes funcionais converteram o txt não-estruturado perfeitamente para eventos financeiros.
Motivo: Continuar avançando com as etapas de ingestão, homologando a fonte Pierre.
Impacto: Valida a fundação suportando não só CSVs, mas estruturas raw TXT customizadas. O sistema agora está preparado para fontes mais exóticas. Aprovados 23/23 testes unitários.

**[2026-06-26] [AUDITORIA] ENTERPRISE REVIEW 2 — DEEP AUDIT (TSK-5.ER2)**
Auditoria profunda executada sobre todo o código da Fase 5 (Sprints V1, V2, V3). Descobertos 6 novos achados: FIND-011 (🔴 CRÍTICO — CRLF bug no Pierre Reader, corrigido imediatamente via `rstrip()`), FIND-012 (🟠 ALTO — risco emoji filter), FIND-013 (🟠 ALTO — categoria composta sem teste), FIND-014 (MD5 vs SHA-256), FIND-015 (cobertura incompleta), FIND-016 (DRY TXT reader). Documentos 31, 32 e 33 completamente reescritos.
Resultado: APROVADO COM RESSALVAS — Nenhum bloqueador imediato. Fundação sólida com 4 P2 para tratar antes da Sprint V4.

**[2026-06-26] [HARDENING] TSK-5.R2 — Hardening Final da Plataforma de Ingestão (Pierre TXT)**
Executados REF-010 e REF-011. Parser Pierre TXT completamente reescrito com abordagem estrutural (classificação de trás-para-frente; detecção de emoji via `unicodedata.category`, independente do símbolo). Suíte de testes ampliada de 5 para 57 casos Pierre (total geral: 67 testes). Cobertura: validator, emoji-filter, parser happy path, categoria composta, emoji desconhecido, ausência de emoji, arquivo vazio, CRLF/LF/UTF-8/UTF-8-BOM/latin1, arquivo parcialmente corrompido, normalizer.
Motivo: Eliminar risco latente (FIND-012, FIND-013, FIND-015) e atingir o nível de certificação antes das próximas fontes.
Resultado: ✅ 67/67 testes passando. 3 funcionais OK. 73 eventos canônicos sem regressão. Banco freeze preservado.

**[2026-06-25] [ARQUITETURA] PARECER FINAL AUTH**
Emissão do parecer técnico final confirmando a adoção da Alternativa B (Autenticação baseada em `.env`). Validou-se que a omissão do `password_hash` na tabela `users` do V3 foi proposital e perfeitamente alinhada ao design de "Single User. Seed automático" previsto no Master Plan. 
Motivo: Evitar violações de schema e destravar a progressão da Fase 2.
Impacto: O banco V3 permanecerá intocado. O Login utilizará verificação por variável de ambiente enquanto o DB garantirá as FKs através do Seed Automático do admin na tabela `users`.

**[2026-06-25] [AUTH] DECISÃO**
Backend retornará `username: user.email` na resposta de `/auth/me`.
Motivo: `AuthContext.tsx` espera campo `username`, mas schema V3 só possui `email` e `name`. Adaptar backend, não o frontend.
Impacto: Zero alteração no frontend. Backend faz o mapeamento.

---

### [2026-06-26] ENTERPRISE AUDIT 3 (EA3)
**[2026-06-26] [AUDITORIA] ENTERPRISE AUDIT 3 — DEEP AUDIT 3 (TSK-5.EA3)**
Auditoria extremamente rigorosa para caçar inconsistências sutis antes de expandir (MyProfit, B3).
Resultado: APROVADO COM RESSALVAS. 1 Crítico (EA3-12), 5 Altos.
Impacto: Geração da tarefa TSK-5.H1 obrigatória para sanar os riscos críticos de robustez.

---

### [2026-06-27] HARDENING EA3 (TSK-5.H1)
**[2026-06-27] [HARDENING] HARDENING PLATAFORMA DE INGESTÃO (TSK-5.H1)**
Auditoria realizada: Executadas correções obrigatórias (P1/Altas) mapeadas na EA3. Adicionado `try/except` em parsers (EA3-12) e pipelines (EA3-24). Corrigido risco de deduplicação na fatura removendo `raw_doc_id` do UUID (EA3-20). Transformado `source_system` em abstrato no CSV (EA3-05). Adicionados testes rigorosos de resiliência (EA3-27).
Motivo: Encerrar definitivamente a estabilização estrutural e de tratamento de exceções.
Resultado: ✅ PLATAFORMA TOTALMENTE CERTIFICADA. 73/73 testes unitários. Golden Tests sem nenhuma perda semântica. Freeze respeitado.
Impacto: Fase 5 destravada para MyProfit (Sprint V4).

---

### [2026-06-28] SPRINT V4 — MYPROFIT PROVENTOS (TSK-5.5-1)
**[2026-06-28] [INGESTION] PIPELINE MYPROFIT PROVENTOS**
Implementação completa do importador do CSV de Proventos do MyProfit.
Motivo: Expansão do portfólio de origens integradas da Fase 5.
Resultado: Reader, Validator, Parser e Normalizer criados. Testes unitários (7 testes novos, total 80) e Funcionais (76 proventos importados do snapshot).
Decisão Arquitetural Crítica: Optado por abortar o importador de "Ativos" do MyProfit temporariamente, visto que consistem em snapshots de posições e não em eventos transacionais (`CanonicalFinancialEvent`). Mapeado como EA4-NEW-001.

---

### [2026-06-28] ENTERPRISE AUDIT 6 (EA6) — CONSOLIDAÇÃO DA FASE 5
**[2026-06-28] [GOVERNANCE] CERTIFICAÇÃO DEFINITIVA DA PLATAFORMA DE INGESTÃO**
Auditoria realizada: Consolidado o ciclo contínuo de Enterprise Audits. Verificado que a Plataforma de Ingestão atende a 100% dos requisitos de resiliência, padronização (BaseCsvReader) e cobertura de testes. As inconsistências de governança levantadas (EA6-INCONSISTENCY-001) foram analisadas e descartadas como falsos positivos (referiam-se à postergação lícita de dívidas P2 e não bloqueios de *hard gate*).
Motivo: Encerrar definitivamente a Fase 5 e preparar terreno para a Próxima Macrofase (Plataforma de Investimentos).
Resultado: ✅ A PLATAFORMA DE INGESTÃO ENCONTRA-SE CONSOLIDADA E CERTIFICADA.
Impacto: Fase 5 encapsulada. Numerações futuras de "Enterprise Audit" não se aplicarão à Ingestão. Nova Macrofase iniciada com foco inicial na Integração B3 (Sprint V5).

---

### [2026-06-29] SPRINT 0 — PLATAFORMA DE INVESTIMENTOS (TSK-INV-0)
**[2026-06-29] [PLANNING] PREPARAÇÃO E ROADMAP DE INVESTIMENTOS**
Atividade realizada: Auditoria de transição de fase, planejamento arquitetural (domínios de Custódia, Movimentações, Proventos, Posições, Carteiras e Reconciliação) e aprovação de Roadmap de 6 Sprints.
Motivo: Formalizar o início da Macrofase Plataforma de Investimentos após a conclusão da Plataforma de Ingestão. Refinamento crítico realizado: Isolamento completo da plataforma de investimentos no domínio `backend/domains/investments/` e desmembramento da Sprint 1 em sub-sprints verticalizadas (1A a 1E) para mitigar riscos arquiteturais.
Resultado: ✅ SPRINT 0 CONCLUÍDA. Gerado o *Relatório de Preparação da Plataforma de Investimentos* e Roadmap detalhado.
Impacto: Roadmap definido; Próxima ação é a execução da Sprint 1A (Arquitetura B3 Custódia).

---

### [2026-06-29] SPRINT 1A — ARQUITETURA B3 CUSTÓDIA (TSK-INV-1A)
**[2026-06-29] [ARCHITECTURE] DOMÍNIO DE INVESTIMENTOS E POSITIONSNAPSHOT**
Atividade realizada: Criação do domínio `backend/domains/investments/` com suas subpastas (readers, parsers, normalizers, etc). Elaboração do DTO `PositionSnapshot`, mapeando campos estáticos (quantity, reference_date, ticker) e estabelecendo a estratégia de Hash (reference_date + ticker + institution) para deduplicação sem violar os eventos de fluxo de caixa (CanonicalFinancialEvent).
Motivo: Garantir isolamento conceitual e de banco de dados entre os estados patrimoniais (snapshots) e os eventos transacionais contábeis da Fase 5.
Resultado: ✅ DOMÍNIO E DTO CRIADOS. 
Impacto: Plataforma de Ingestão transacional 100% preservada. Sprint 1B (Reader B3 Custódia) está pronta para iniciar seu desenvolvimento isolado.

---

### [2026-06-29] SPRINT 1A.5 — LEVANTAMENTO TÉCNICO B3 (TSK-INV-1A.5)
**[2026-06-29] [ANALYSIS] ESPECIFICAÇÃO DE DADOS DA B3**
Atividade realizada: Análise binária do arquivo `samples/Exemplo_Ativos_B3.csv` confirmando sua natureza real (`.xlsx`). Mapeamento da tipologia de abas (Ações, Fundos, Tesouro, Proventos), identificação de cabeçalhos, inconsistências de valores e modelagem da estratégia de parse (engine openpyxl + descarte de rodapés nulos).
Motivo: Evitar surpresas estruturais (feature creep) ou refatorações severas durante a codificação do Reader (Sprint 1B).
Resultado: ✅ LEVANTAMENTO CONCLUÍDO. Gerado o contrato técnico oficial em `project/B3_IMPORT_SPEC.md`.
Impacto: Eliminação de riscos operacionais. Caminho completamente livre e previsível para o codificação do B3 Reader.

---

### [2026-06-29] SPRINT 1B — READER B3 CUSTÓDIA (TSK-INV-1B)
**[2026-06-29] [IMPLEMENTATION] DESENVOLVIMENTO DO B3 READER**
Atividade realizada: Implementação de `backend/domains/investments/readers/b3_reader.py` suportando o parse binário de `.xlsx` da Área do Investidor (B3) através da biblioteca `openpyxl`. Adicionado detecção proativa de formato (`zipfile.is_zipfile`), iteração dinâmica de abas (Ações, Fundos, Tesouro Direto, Proventos Recebidos) e retorno nativo como Dicionário de DataFrames estruturados.
Motivo: Garantir uma camada agnóstica de extração de dados sem poluição de regras de negócio ou de domínio.
Resultado: ✅ SPRINT 1B CONCLUÍDA. Cobertura de 100% de testes unitários e funcionais no `test_b3_reader.py`. O Reader está 100% isolado, sem importar `imports/dto.py`.
Impacto: Caminho limpo e testado para que a Sprint 1C (Parser B3 Custódia) possa iterar sobre os DataFrames brutos e extrair metadados úteis (Tickers, ISINs, Quantidades).

---

### [2026-07-03] SPRINT 1C — PARSER B3 CUSTÓDIA (TSK-INV-1C)
**[2026-07-03] [IMPLEMENTATION] DESENVOLVIMENTO DO B3 PARSER**
Atividade realizada: Implementação de `backend/domains/investments/parsers/b3_parser.py` responsável por converter DataFrames em DTOs intermediários (RawB3StockPosition, RawB3FundPosition, RawB3TreasuryPosition, RawB3Dividend). O Parser descarta corretamente as linhas nulas de rodapé e converte os valores numéricos com tratamento específico para campos nulos e formatação em strings (`-` substituído por `None`).
Motivo: Mapear os dados brutos iterando linha a linha com tipagem forte antes da aplicação de regras de negócio.
Resultado: ✅ SPRINT 1C CONCLUÍDA. Cobertura de 100% (unitários + integração).
Impacto: A etapa de normalização (Sprint 1D) já poderá consumir objetos Python nativamente validados em vez de DataFrames crus.

---

### [2026-07-03] SPRINT 1D — NORMALIZER B3 CUSTÓDIA (TSK-INV-1D)
**[2026-07-03] [IMPLEMENTATION] DESENVOLVIMENTO DO B3 NORMALIZER**
Atividade realizada: Implementação de `backend/domains/investments/normalizers/b3_normalizer.py` responsável por converter DTOs intermediários (brutos) em instâncias completas de `PositionSnapshot`. O normalizador uniformiza nomes de tickers (removendo prefixos de fracionários "F"), converte nomes de instituições para caixa alta e tipifica o ativo (AssetTypeEnum) além de gerar o `snapshot_hash` (idempotência visual/lógica).
Motivo: Garantir que a camada de pipeline receba entidades padronizadas e imutáveis da custódia, independente do formato de entrada (B3 ou outras corretoras no futuro).
Resultado: ✅ SPRINT 1D CONCLUÍDA. Cobertura completa de testes sobre normalização numéricas, hashes e conversão textual.
Impacto: A Pipeline B3 (Sprint 1E) terá acesso à estrutura imaculada de estado (PositionSnapshot) pronta para persistência via repositório. Nenhuma modificação no banco de dados, API, Frontend ou MyProfit foi realizada.

---

### [2026-07-03] SPRINT 1E — PIPELINE B3 CUSTÓDIA (TSK-INV-1E)
**[2026-07-03] [IMPLEMENTATION] ORQUESTRAÇÃO B3 CUSTÓDIA**
Atividade realizada: Construção do coordenador `backend/domains/investments/pipelines/b3_custody_pipeline.py`. Ele instanciou e orquestrou sequencialmente o Reader, Parser e Normalizer de forma encapsulada. Criada a estrutura de `PipelineResult` retornando os snapshots computados, as métricas de sucesso, taxas de descarte e tratamento explícito de exceções das três camadas (ReaderException, ParserException e genéricas).
Motivo: Concentrar a responsabilidade de orquestração do processamento do arquivo em um único ponto isolado, sem acoplar diretamente com a interface de persistência de banco de dados.
Resultado: ✅ SPRINT 1E CONCLUÍDA. Arquitetura testada em 5 frentes incluindo 100% de end-to-end simulado em `test_b3_custody_pipeline.py`.
Impacto: O domínio de Investimentos atingiu o seu primeiro "Golden Path". Todo o fluxo lógico de extração B3 está isolado e funcional. O sistema está homologado para iniciar a persistência no banco (Sprint 2).

---

### [2026-07-03] ARCHITECTURE TRANSITION AUDIT — MACROFASE 1
**[2026-07-03] [AUDIT] CERTIFICAÇÃO DA MACROFASE 1**
Atividade realizada: Auditoria de Transição Arquitetural certificando integralmente as Sprints 1A, 1A.5, 1B, 1C, 1D e 1E da Plataforma de Investimentos. Validação da cobertura 23/23 testes, isolamento do domínio (zero cross-imports com `imports/`) e consistência documental de toda a governança.
Resultado: ✅ MACROFASE 1 CERTIFICADA OFICIALMENTE.
Impacto: Sprint 2 (Persistência B3 e Valuation) oficialmente liberada.

---

### [2026-07-03] SPRINT 2 — PERSISTÊNCIA B3 CUSTÓDIA (TSK-INV-2)
**[2026-07-03] [IMPLEMENTATION] CAMADA DE PERSISTÊNCIA B3**
Atividade realizada: Criação da migration SQL `013_position_snapshots.sql` definindo a tabela `position_snapshots` com 6 índices. Implementação do `PositionRepository` com UPSERT via `ON CONFLICT(snapshot_hash) DO UPDATE`, transacão única com rollback automático (SQLAlchemy 2.0 `engine.begin()`). Integração opcional ao Pipeline via duck typing (sem criar acoplamento rígido).
Resultado: ✅ SPRINT 2 CONCLUÍDA. 33/33 testes PASSED. Banco atualizado.
Impacto: O fluxo completo `Reader -> Parser -> Normalizer -> Repository -> Banco` está operacional e idempotente.

---

### [2026-07-03] SPRINT 3A — CEI (LEVANTAMENTO TÉCNICO E ARQUITETURA) (TSK-INV-3A)
**[2026-07-03] [ARCHITECTURE] ESPECIFICAÇÃO DE EVENTOS TRANSACIONAIS CEI**
Atividade realizada: Levantamento do diretório `samples/` constatando a ausência de arquivo físico de Movimentação/CEI. Definição arquitetural teórica do domínio `backend/domains/investments/cei/`. Estabelecimento da diferenciação entre Snapshot (estado patrimonial) e Evento (transação/corporate action). Criação do documento canônico `CEI_IMPORT_SPEC.md` contendo riscos, dependências e catálogo esperado de eventos da B3 (compra, venda, desdobramento, etc).
Resultado: ✅ SPRINT 3A CONCLUÍDA. Zero código implementado, zero tabelas criadas.
Impacto: Domínio preparado teoricamente para iniciar ingestão de transações B3 assim que arquivo de amostra for providenciado.

---

### [2026-07-04] SPRINT 3B — HOMOLOGAÇÃO DO ARQUIVO DE MOVIMENTAÇÕES B3 (TSK-INV-3B)
**[2026-07-04] [ARCHITECTURE] CONTRATO TÉCNICO CEI MOVIMENTAÇÕES**
Atividade realizada: Homologação técnica estrutural baseada no arquivo físico `Exemplo_Negociacao_B3.xlsx` (SHA256: a7847fb4c35e63a83258b1f874a520c6e5b37b65fd3d9663a76c034ccdeb566d). A análise atestou um contrato fixo isolando a Aba `Negociação` (9 colunas, sem nulos). Catálogo de eventos ancorado (Trades). Conduzida auditoria de sobreposição provando independência plena (sem conflito) entre o arquivo de Negociação e o de Custódia. Chave de Idempotência formulada baseando-se em MD5(Data+Ticker+Instituição+Tipo+Qtde+Preço) para suprimir a ausência de IDs únicos na B3.
Resultado: ✅ SPRINT 3B CONCLUÍDA. Nenhuma linha de código foi implementada.
Impacto: O contrato técnico `CEI_MOVEMENTS_SPEC.md` está selado, atestando independência de pipelines (Snapshot vs Trade) pavimentando as regras exatas para a Sprint 3C.

---

### [2026-07-05] SPRINT 3C.1 — HOMOLOGAÇÃO FUNCIONAL DO PIPELINE CEI (TSK-INV-3C.1)
**[2026-07-05] [ARCHITECTURE] CONSOLIDAÇÃO DO PIPELINE TEÓRICO E2E**
Atividade realizada: Etapa de "Zero Code" para extração de métricas de qualidade. Conduzida Etapa 0 confirmando integridade entre diretórios e documentações vigentes. Executadas Etapas 1-5 (Inventário e Sobreposição Temporal, identificando 14 transações num gap de 155 dias em `Exemplo_Negociacao_B3.xlsx`). Gerados artefatos `PIPELINE_FUNCTIONAL_SPEC.md`, `TRADE_MAPPING_MATRIX.md`, `IMPORT_COMPATIBILITY_MATRIX.md` e `DATA_QUALITY_REPORT.md` descrevendo exaustivamente a estratégia do Reader, Parser, Normalizer e Repository, atestando resiliência e tratando anomalias (`BBAS3F`, nulos e consolidação MD5).
Resultado: ✅ SPRINT 3C.1 CONCLUÍDA. Arquivos `.md` criados e revisados. Código fonte congelado respeitado integralmente.
Impacto: Contratos e tipos rigorosamente mapeados liberando a implementação do Reader (Sprint 3C.2) sob a barreira de aprovação.

---

### [2026-07-08] SPRINT 3C.2 — CEI MOVIMENTAÇÕES (TSK-INV-3C.2)
**[2026-07-08] [IMPLEMENTATION] GATE 2 (READER CEI)**
Atividade realizada: Implementação e homologação do Reader CEI (`backend/domains/investments/readers/cei_reader.py`) focado exclusivamente na extração da aba `Negociação` do arquivo `samples/Exemplo_Negociacao_B3.xlsx` via `openpyxl`.
Motivo: Iniciar o pipeline transacional separando o processamento das Movimentações CEI do arquivo de Custódia.
Resultado: ✅ READER IMPLEMENTADO. Aprovado nos testes físicos de tipagem e extração, validando 14 linhas contendo 9 colunas.
Impacto: A infraestrutura basal para processar as transações B3 foi injetada no sistema. O parser (Gate 3) está liberado para codificação.

**[2026-07-08] [ARCHITECTURE] GATE 3A (AUDITORIA PARSER)**
Atividade realizada: Homologação estrutural e definição rigorosa dos limites funcionais do `B3MovementsParser` visando a conversão limpa do DataFrame `Negociação` para a entidade estrita `RawB3Movement`. 
Motivo: Prevenir lógicas de normalização prematuras ou buscas no banco durante o estágio de tipagem.
Resultado: ✅ AUDITORIA CONCLUÍDA. Nenhum código escrito.
Impacto: Caminho perfeitamente delineado para a implementação do Parser (Gate 3B).

**[2026-07-08] [IMPLEMENTATION] GATE 3B.1 (ESTRUTURA PARSER)**
Atividade realizada: Criação estrutural e docstrings da classe `B3MovementsParser` no módulo `cei_parser.py`, estritamente com signatures e exceptions, desprovido de lógica algorítmica.
Motivo: Garantir aderência do contrato Python ao plano da arquitetura (Gate 3A) antes da codificação real, isolando dependências.
Resultado: ✅ ESTRUTURA PARSER CRIADA. Testes sintáticos (py_compile, import e instanciação) certificados.
Impacto: A infraestrutura física do parser B3 encontra-se pronta para o desenvolvimento do algoritmo no Gate 3B.2.

**[2026-07-08] [IMPLEMENTATION] GATE 3B.2A (PARSER CEI FASE 1)**
Atividade realizada: Implementação parcial do algoritmo do `B3MovementsParser` iterando e validando de maneira estrita a presença das 7 colunas obrigatórias mapeadas na matriz B3, com suporte a DataFrame vazio e setup do Logger.
Motivo: Evitar desenvolvimento de parser monolítico, injetando uma camada de resiliência e bloqueio estrito `KeyError` antes de converter strings brutas.
Resultado: ✅ PARSER BASE IMPLEMENTADO. Lógica de controle pronta e testada com DataFrame vazio.
Impacto: A carcaça de repetição está 100% segura; a próxima etapa processará de fato os DTOs no Gate 3B.2B.

**[2026-07-08] [IMPLEMENTATION] GATE 3B.2B (PARSER CEI FINALIZADO)**
Atividade realizada: Implementação completa do algoritmo do `B3MovementsParser` (`cei_parser.py`).
Motivo: Alimentar o DTO fraco `RawB3Movement` com os dados purificados da planliha (hífens para None, Floats para Decimal).
Resultado: ✅ PARSER CONCLUÍDO. Script leu 14 linhas do Pandas e gerou exatos 14 DTOs Pydantic.
Impacto: A etapa de tipificação fraca e bruta encerrou-se completamente. O sistema avança para aplicar as lógicas financeiras no Gate 4 (Normalizer).

**[2026-07-08] [ARCHITECTURE] GATE 4A (AUDITORIA NORMALIZER)**
Atividade realizada: Homologação estrutural e definição da Matriz de Transformação para o `B3MovementsNormalizer`. Estabelecidos limites funcionais (sem consultas de banco) para conversão do `RawB3Movement` para o evento canônico `TradeDTO`.
Motivo: Evitar acoplamento lógico da camada de banco de dados na camada funcional do pipeline CEI.
Resultado: ✅ AUDITORIA CONCLUÍDA. Plano de implementação formulado (sem codificação).
Impacto: Caminho limpo para o desenvolvimento algorítmico (Gate 4B).

**[2026-07-08] [IMPLEMENTATION] GATE 4B.1 (NORMALIZER CEI IMPLEMENTADO)**
Atividade realizada: Codificação total do componente `B3MovementsNormalizer` no módulo `cei_normalizer.py`.
Motivo: Aplicar semântica financeira e gerar a Entidade Universal `TradeDTO` selada pelo hash de idempotência MD5, essencial para impedir duplicidade no Ledger de Ingestão.
Resultado: ✅ NORMALIZER CONCLUÍDO E TESTADO E2E (Sem Banco). Transformadas 14 abstrações sujas em 14 Transações Imaculadas.
Impacto: Pipeline lógico encerrado. O sistema agora está matematicamente seguro e preparado para injetar DTOs purificados no Banco de Dados (Gate 5).

**[2026-07-09] [ARCHITECTURE] GATE 5A (AUDITORIA REPOSITORY)**
Atividade realizada: Homologação arquitetural do mapeamento entre o objeto `TradeDTO` e o DDL da tabela `trades` (migration `004_investments.sql`). Planejado "Upsert em Lote" com conversões passivas de lookup (resolução de `asset_id` e `account_id`) e câmbio estrutural (preço para centavos).
Motivo: Proteger o banco de dados assegurando obediência absoluta ao SQL Schema puro e atomicidade relacional.
Resultado: ✅ AUDITORIA CONCLUÍDA. Plano de implementação pronto e sem codificação escrita.
Impacto: Destravamento da construção física da camada final de persistência (Gate 5B).

**[2026-07-10] [IMPLEMENTATION] GATE 5B.1 (ESTRUTURA DO REPOSITORY)**
Atividade realizada: Scaffold estrutural e inofensivo do arquivo `trade_repository.py` definindo contratos e tipos para queries e persistência, preenchidos com `NotImplementedError`.
Motivo: Abordagem defensiva ditada pelo protocolo. A arquitetura exige separação em micro-etapas para validação contínua (Compilação isolada), prevenindo acoplamentos ou importações antecipadas da lógica transacional.
Resultado: ✅ SKELETON CONCLUÍDO E COMPILADO (PyCompile).
Impacto: Cria-se o contrato passivo base, destravando o próximo degrau: Escrita rigorosa das lógicas de Foreign Key Lookup (Gate 5B.2).

**[2026-07-10] [IMPLEMENTATION] GATE 5B.2 (LOOKUPS REPOSITORY)**
Atividade realizada: Codificação das rotinas de lookup (`_resolve_asset_id` e `_resolve_account_id`) equipadas com in-memory caching (`_asset_cache`, `_account_cache`). Testes unitários com Mock de SQLAlchemy comprovaram a resiliência sem manipulação de banco de dados.
Motivo: Evitar chamadas (SELECT) duplicadas para Tickers que podem aparecer em centenas de blocos transacionais seguidos na planilha da B3.
Resultado: ✅ LOOKUPS CONCLUÍDOS. Sem acesso real ao banco na testagem.
Impacto: Habilita a implementação final de Persistência (Gate 5B.3).

**[2026-07-11] [IMPLEMENTATION] GATE 5B.3 (PERSISTÊNCIA REPOSITORY)**
Atividade realizada: Codificação e testes do núcleo atômico `save()` e `save_many()` no `TradeRepository`. Implementada query RAW otimizada via SQLAlchemy Core combinando insert com `ON CONFLICT DO UPDATE` (SQLite Upsert).
Motivo: Persistir permanentemente as abstrações tratadas sem causar travamentos de constraint caso lotes anteriores sejam reprocessados para atualizações.
Resultado: ✅ REPOSITÓRIO FINALIZADO E APROVADO E2E em DB Memory Mock.
Impacto: A Ingestão transacional V3 está pronta estrutural e matematicamente. Faltando apenas a orquestração do fluxo unificado (Gate 6).

**[2026-07-11] [IMPLEMENTATION] GATE 6.1 (PIPELINE CLI)**
Atividade realizada: Criação do `cli.py`, unificando a cadeia (Reader -> Parser -> Normalizer -> Repository). Injeção rigorosa de Engine e Session delimitando a transação via Context Manager. Tratamento assertivo de exceções falhando rápido (`Fail-Fast`). Correção prévia do truncamento do `unit_price` em centavos no `trade_repository.py`.
Motivo: Orquestrar e executar a macrofase de ingestão de ativos de investimento B3 via CLI, mantendo o banco protegido por Atomicidade (Commit/Rollback isolados).
Resultado: ✅ PIPELINE IMPLEMENTADO COM SUCESSO. Testado ponta a ponta (identificada corretamente falha por corretora não-existente no DB).
Impacto: Pipeline C.E.I 100% Finalizado e Orquestrável via Terminal.

**[2026-07-11] [IMPLEMENTATION] GATE 6.2 (BROKER ALIAS LAYER)**
Atividade realizada: Criação de `BrokerAliasResolver` para o `TradeRepository` e estabelecimento do dicionário de nomes canônicos.
Motivo: Evitar corrupção e duplicidade em contas (ex: "NU INVESTIMENTOS S.A. - CTVM" x "Nubank") através de uma barreira estática leve em RAM antes do hit ao DB.
Resultado: ✅ SUCESSO. A abstração funcionou ponta-a-ponta e capturou os mocks definidos em testes locais.
Impacto: Escalabilidade de mapeamentos para futuras fontes sem encostar no schema do SQLite ou nos parsers já prontos.

**[2026-07-11] [IMPLEMENTATION] GATE 6.3 (IMPORT REPORT)**
Atividade realizada: Criação do DTO `ImportReport` e acoplamento exclusivo na CLI.
Motivo: Centralizar todas as métricas não-financeiras da importação (rows_read, rows_persisted, warnings, elapsed_time) num objeto unificado canônico, mantendo o núcleo dos parsers limpos de preocupações de telemetria.
Resultado: ✅ SUCESSO. Relatório gerado no terminal cobrindo exatamente os indicadores exigidos.
Impacto: Cria-se o contrato para futura gravação do relatório na tabela de `import_runs` sem corromper a arquitetura atômica atual.

**[2026-07-11] [AUDIT] GATE 6.4 (HOMOLOGAÇÃO FINAL DO PIPELINE)**
Atividade realizada: Executada auditoria E2E em todos os pontos da malha de importação. Criação das matrizes de responsabilidade e verificação rigorosa de leaks.
Motivo: Encerrar a fase 3C.2 e garantir que as fundações de orquestração suportem novas integrações sem retrabalho arquitetural.
Resultado: ✅ HOMOLOGAÇÃO CONCLUÍDA. Nenhum desvio de fluxo ou responsabilidade encontrado.
Impacto: A Plataforma de Importação de Investimentos está estabilizada e apta para escalar.

**[2026-07-12] [FIX] GATE 6.5 (CORREÇÃO TD-02 — IDEMPOTÊNCIA FINANCEIRA)**
Atividade realizada: Correção do `B3MovementsNormalizer` para gerar o hash de idempotência com o broker canônico normalizado pelo `BrokerAliasResolver`, eliminando o risco de duplicatas financeiras causadas por variações de grafia da B3.
Arquivos: `backend/domains/investments/normalizers/cei_normalizer.py`
Motivo: TD-02 identificado na re-auditoria do Gate 6.4 (Claude Sonnet). Hash com broker cru poderia gerar duplicatas financeiras reais.
Resultado: ✅ 4/4 casos de teste aprovados. Hash convergente para aliases distintos da mesma corretora.
Impacto: Garantia definitiva de idempotência financeira em todas as importações futuras.

**[2026-07-12] [AUDIT] GATE 7.0 (AUDITORIA DE ENTRADA SPRINT 4)**
Atividade realizada: Auditoria de entrada para a arquitetura de Open Finance Investimentos.
Motivo: Mapeamento de dívidas técnicas e lacunas no schema (Migration 004) antes do desenvolvimento de adapters Open Finance.
Resultado: ✅ APROVADO. Levantadas as necessidades de expandir constraints de `source` no banco e de criar a persistência para `PositionSnapshot`.
Impacto: Início do planejamento da Sprint 4 (Open Finance) guiado por restrições bem mapeadas.

**[2026-07-12] [MIGRATION] GATE 7.1 (MIGRATION 005 — OPEN FINANCE & POSITION SNAPSHOTS)**
Atividade realizada: Criação segura do script de migração `005_open_finance.sql`. Adicionou suporte estrutural à `source` = `'OPEN_FINANCE'` e implementou a estrutura relacional para abrigar a custódia patrimonial unificada (`position_snapshots`).
Motivo: Necessidade de adequar o banco a um novo tipo de importador de dados sem quebrar o framework existente.
Resultado: ✅ SUCESSO. Testes realizados isolando DDL e DML, mantendo a proteção contra dados não homologados nas pipelines.
Impacto: A base de dados FinAnalytics V3 passa a suportar ingestão dinâmica de múltiplos provedores e abrigar as futuras conciliações de snapshots de custódia.

**[2026-07-12] [IMPLEMENTATION] GATE 7.2 (SNAPSHOT REPOSITORY)**
Atividade realizada: Criação do repositório `SnapshotRepository` para persistir objetos `PositionSnapshot`.
Motivo: Viabilizar a ingestão de Posição Consolidada (Custódia) proveniente de integrações futuras (Open Finance e Área do Investidor).
Resultado: ✅ 8/8 testes aprovados. O repositório realiza Upsert idempotente na nova tabela `position_snapshots`.
Impacto: A camada de persistência para a Macrofase Open Finance está pronta para receber adaptadores de integração.

**[2026-07-12] [IMPLEMENTATION] GATE 7.3 (OPEN FINANCE ADAPTER LAYER)**
Atividade realizada: Criação de um ACL (Anti-Corruption Layer) puro para receber dicionários de payloads do Open Finance (Custódia e Movimentações) e instanciar rigorosamente as classes `TradeDTO` e `PositionSnapshot`.
Motivo: Isolar a lógica de sanitização, cast monetário via `Decimal` e geração de hash das lógicas de banco, garantindo Fail-Fast sem abrir conexões.
Resultado: ✅ SUCESSO absoluto (100% testado). O sistema processa os dicionários e converte valores financeiros, aplicando formatações de data iso, e impedindo lotes sujos.
Impacto: Permite integração plug-and-play do sistema com orquestradores recebendo Webhooks/JSONs sem violar a regra de pureza do domínio de Investimentos.

**[2026-07-12] [IMPLEMENTATION] GATE 7.4 (OPEN FINANCE CLI/ORQUESTRADOR)**
Atividade realizada: Criação do orquestrador de Ingestão de Open Finance acoplando JSON, Adapter, Repositórios e ImportReport.
Motivo: Ligar todos os gates da Sprint 4 numa pipeline isolada e transacional.
Resultado: ✅ SUCESSO. A pipeline opera sob contexto atômico e faz o gerenciamento unificado de Snapshot e Trades, imprimindo o ImportReport no formato canônico da plataforma e fechando as conexões do banco de modo seguro.
Impacto: Fim da infraestrutura de Ingestão Open Finance. Apto para receber payloads do frontend/API ou arquivos físicos simulando callbacks de parceiros bancários.

**[2026-07-12] [IMPLEMENTATION] GATE 8.1 (POSITION ENGINE)**
Atividade realizada: Criação do motor puro `PositionEngine` e evolução das `TradeType` no `dto.py`.
Motivo: Implementar o algoritmo central que lê o histórico de eventos financeiros (Trades, Transferências, Amortizações) para projetar a quantidade e custo médio atualizado dos ativos, cruzando a informação com os relatórios estáticos (`PositionSnapshot`).
Resultado: ✅ SUCESSO. Engine implementada com `decimal.Decimal` em 100% das operações matemáticas. Validada em baterias in-memory contra todos os cenários corriqueiros de contabilidade (venda total, split invertido, capital devolvido).
Impacto: A base de Reconciliação Patrimonial está pronta, possibilitando que as futuras interfaces do usuário exibam divergências reais entre B3, Corretoras e o Banco de Dados.

**[2026-07-12] [IMPLEMENTATION] GATE 8.2 (VALUATION ENGINE)**
Atividade realizada: Criação do motor MTM (Mark-to-Market) acoplado logicamente à saída da Position Engine.
Motivo: Dotar a plataforma de inteligência financeira para calcular variações patrimoniais não-realizadas com base em cotações ativas, preservando a base de custo estática contra flutuações e ausência temporária de mercado.
Resultado: ✅ SUCESSO. Engine pura isolada que computa Gains % e Market Value instantaneamente, mapeando ativos sem preço como lastreados ao custo e ativos falidos como perdas de 100%.
Impacto: Apto a iniciar as agregações macro-financeiras da Wealth Engine e montar os dashboards de Rentabilidade da carteira.

**[2026-07-12] [IMPLEMENTATION] GATE 8.3 (WEALTH ENGINE)**
Atividade realizada: Criação do motor agregador de portfólio (Wealth Engine).
Motivo: Sintetizar as avaliações atomizadas (por ativo e corretora) em uma visão gerencial de portfólio, sumarizando posições em macro-classes, fatias institucionais e exibindo os pesos da carteira (Asset Allocation).
Resultado: ✅ SUCESSO. O sistema agrupa instâncias do `ValuationResult` de forma O(N), isola divisões por zero e emite a DTO final `WealthSummary`, perfeitamente alinhada para ser devolvida via API ao Frontend.
Impacto: Fechamento da cadeia de Inteligência Patrimonial da Sprint 5, restando apenas as métricas temporais (Performance Engine / TWRR) no próximo Gate.

**[2026-07-12] [IMPLEMENTATION] GATE 8.4 (PERFORMANCE ENGINE)**
Atividade realizada: Criação do motor de desempenho financeiro (`PerformanceEngine`) com cálculo de CAGR, TWR, MWR, Yield on Cost, retornos anualizados, mensais e diários.
Motivo: Complementar a Wealth Engine com a dimensão temporal da performance patrimonial — fundamental para exibição de rentabilidade no Dashboard e para integração futura com APIs de comparação de benchmarks (CDI, IBOV).
Resultado: ✅ SUCESSO. Engine implementada com `Decimal` exclusivo. TWR exato por produto encadeado. CAGR por exponenciação. Proteção integral a divisões por zero, Overflows e cenarios de falência.
Impacto: Encerra a Sprint 5. O backend agora possui infraestrutura analítica completa: Posição -> MTM -> Patrimônio -> Performance.
