# Relatório de Execução - TSK-GOV-01
**Sprint de Integração da Governança**

## 1. Arquitetura Anterior
- **Frontend**: O frontend possuía abas rígidas para MyProfit e Pierre, forçando o usuário a interagir com componentes separados. Havia forte dependência de APIs paralelas como `/import-pierre` e `/import-myprofit`.
- **Backend**: Existiam rotas isoladas (`/import-pierre`, `/import-myprofit`) com lógicas fragmentadas para cada origem.
- **Dashboard e Lista**: O dashboard chamava uma rota inexistente (`/governance/dashboard`) ou consumia mocks estáticos na listagem de importações (`/governance/imports`), ignorando a tabela SQLite `import_runs`.

## 2. Arquitetura Final
- **Frontend**: Consolidação em um fluxo de **Origem Única** (Dropdown de Seleção). Um único formulário lida com os 6 tipos de arquivos suportados (Nubank Conta/Fatura, MyProfit Proventos/Evolução, Pierre e B3), respeitando o formato de *Select -> Upload -> Preview*.
- **Backend**: Unificação na rota `POST /api/v1/governance/imports/upload`.
- **Dashboard e Lista**: O backend agora lê **100% da tabela `import_runs`** e faz agregação real dos status (`PENDING`, `SUCCESS`, `PARTIAL`, `FAILED`), traduzindo para o Frontend sem quebrar os crachás (badges) visuais (`CONFIRMED`, `AWAITING_CONFIRMATION`, etc).

## 3. Contratos e Endpoints Alterados
- **Removidos**: `POST /import-pierre`, `POST /import-myprofit`
- **Criado**: `POST /imports/upload` usando um DTO genérico `UploadPayload` (`file_name`, `raw_text`, `source_type`).
- **Modificados**: 
  - `GET /governance/dashboard`: Adicionado agregador SQLite real, retorna o DTO `DashboardMetrics`.
  - `GET /governance/imports`: Adicionada query SQLite real com fallback de tradução de `rows_errored` para `rows_failed`.
  - `GET /governance/imports/{run_id}`: Lê do banco real, traduzindo hashes de arquivos.
  - `GET /governance/imports/{run_id}/staging-items`: Lê o JSON salvo em `import_artifacts` e extrai `ticker`/`descricao` via *duck typing* nativo.

## 4. Componentes e Hooks Alterados
- **Componente**: `frontend/src/app/governance/imports/page.tsx`
- **Modificações**:
  - Removido `activeTab` e os botões de tabulação.
  - Introduzido `<select>` para `sourceType`.
  - Adicionado suporte dinâmico para leitura via API única.

## 5. Testes Executados (E2E)
- **Cenário**: Login Admin -> Navegação `/governance/imports` -> Upload NUBANK_CONTA, PIERRE, MYPROFIT_PROVENTOS, B3 -> Validação -> Revisão -> Confirmação.
- **Ferramenta**: Playwright (Python Engine Chromium).
- **Resultados**: 
  - Os 4 arquivos reais de `samples/` foram lidos com sucesso.
  - O Backend identificou os tipos.
  - O SQLite registrou as `import_runs` com as quantidades corretas de linhas.
  - A interface renderizou a Preview adequadamente e a importação foi aceita.

## 6. Evidências
- As screenshots do E2E estão salvas como `project/dashboard_evidencia.png`.
- Os scripts de automação validaram o processamento e o console não apontou quebras de contrato.

## 7. Pendências e Próximos Passos
- **Status do Banco**: O DTO agora reflete o banco, mas a visualização detalhada da Revisão (onde se edita ticker manual) será testada a fundo na **TSK-GOV-02** (Revisão & Staging).
- **Aprovação**: Aguarda validação do usuário. Caso aprovado, o projeto deve prosseguir exatamente na ordem estipulada pela Fila de Implementação: **TSK-GOV-02**.
