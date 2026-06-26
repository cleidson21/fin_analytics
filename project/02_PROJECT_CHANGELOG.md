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

**[2026-06-25] [ARQUITETURA] PARECER FINAL AUTH**
Emissão do parecer técnico final confirmando a adoção da Alternativa B (Autenticação baseada em `.env`). Validou-se que a omissão do `password_hash` na tabela `users` do V3 foi proposital e perfeitamente alinhada ao design de "Single User. Seed automático" previsto no Master Plan. 
Motivo: Evitar violações de schema e destravar a progressão da Fase 2.
Impacto: O banco V3 permanecerá intocado. O Login utilizará verificação por variável de ambiente enquanto o DB garantirá as FKs através do Seed Automático do admin na tabela `users`.

**[2026-06-22] [AUTH] DECISÃO**
Backend retornará `username: user.email` na resposta de `/auth/me`.
Motivo: `AuthContext.tsx` espera campo `username`, mas schema V3 só possui `email` e `name`. Adaptar backend, não o frontend.
Impacto: Zero alteração no frontend. Backend faz o mapeamento.
