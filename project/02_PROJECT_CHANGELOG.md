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

**[2026-06-22] [AUTH] DECISÃO**
Backend retornará `username: user.email` na resposta de `/auth/me`.
Motivo: `AuthContext.tsx` espera campo `username`, mas schema V3 só possui `email` e `name`. Adaptar backend, não o frontend.
Impacto: Zero alteração no frontend. Backend faz o mapeamento.
