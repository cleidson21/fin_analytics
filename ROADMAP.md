# fin_analytics_v2 — Roadmap

> Documento vivo. Atualizar status conforme progresso.
> Legenda: ✅ Concluído · 🔄 Em andamento · ⬜ A fazer · 🆕 Adicionado · 🔮 Futuro/Backlog

---

## Status geral

| Módulo | Status |
|---|---|
| Controle Financeiro | ✅ Funcional |
| Módulo Wealth | ✅ Funcional (polish concluído) |
| Governança de Importação | ✅ Concluído (Staging, Review, Rollback) |
| Importação CSV | ✅ Concluído |
| Administração do banco | ✅ Concluído |
| Governança dos dados | 🔄 Próximo |
| MVP Stabilization | ⬜ Próximo |
| Backup e Restore | ⬜ Próximo |
| Docker | ⬜ Próximo |
| Metas financeiras | ⬜ Planejado |
| Automação Gemini | ⬜ Planejado |
| Market Data / YFinance | ⬜ Planejado |
| Central de Insights | ⬜ Planejado |
| Segurança e testes | ⬜ Planejado |
| CI/CD e documentação | ⬜ Planejado |

---

## Sequência recomendada

```
1.  Polish Wealth / UI (Fase 0)                ✅ Concluído
2.  Governança de Importação (Fase 0.5)        ✅ Concluído (Staging e Promoção Atômica)
3.  Importação definitiva CSV MyProfit (Fase 1) ✅ Concluído
4.  Administração do banco (Fase 2) ✅ Concluído
5.  Governança dos dados (Fase 3) ← fazer AGORA
6.  MVP Stabilization (Fase 4)
7.  Backup e Restore (Fase 5)
8.  Docker + Documentação básica (Fase 6)
9.  Metas financeiras (Fase 7)
10. Python-GenAI — automação Pierre (Fase 8)
11. Market Data / YFinance (Fase 9)
12. Central de Insights (Fase 10)
13. Testes (unitários + integração + E2E) (Fase 11)
14. Auditoria de segurança (Fase 11)
15. CI/CD (Fase 6, complemento)
16. Open Finance
17. IA Conversacional
18. Planejamento FIRE
19. Relatório IRPF
```

**Por que Fase 0.5 antes de tudo?**
Hoje o fluxo é `CSV → Parser → Banco`. Daqui a 3 fases será
`MyProfit + Pierre + Gemini + Open Finance + YFinance → mesma infraestrutura`.
Construir a rastreabilidade agora evita refatorar a camada de importação após cada nova fonte.
A Fase 1 (drag-and-drop) nasce muito mais limpa se `import_runs` e `import_artifacts` já existirem.

---

## ✅ Concluído

### Controle Financeiro

- ✅ Dashboard principal (visão geral, indicadores)
- ✅ Transações
- ✅ Categorias
- ✅ Parcelamentos
- ✅ Relatórios

### Módulo Wealth

- ✅ Executive Home
- ✅ Patrimônio
- ✅ Alocação
- ✅ Dividendos 
- ✅ Evolução

### Polish aplicado (Fase 0)

- ✅ Filtro de período como pill-group contido
- ✅ Paleta semântica no Treemap de alocação (RF=#4ecf98, Ações=#7EB8F7, FIIs=#7F77DD, Exterior=#f5a623)
- ✅ KPI cards com valor numérico real (removido placeholder "Consolidado")
- ✅ Marcos patrimoniais como timeline com progresso para próximo marco
- ✅ Unificar topbar do módulo Wealth com pills com dot colorido
- ✅ Corrigir idioma dos subtítulos (removidos prefixos em inglês)
- ✅ Sub-labels dos KPI cards: dado comparativo → badge colorido / descritivo → text muted
- ✅ Benchmark toggle com cor da linha ativa e linhas inativas em opacity 0.35
- ✅ Card "Insight de Risco" do Executive Home com mini donut + Concentração Top 5

---

## ✅ Fase 0.5 — Governança de Importação e Rastreabilidade 🆕

**Objetivo:** criar a infraestrutura genérica que todas as fontes de dados vão usar.
Não implementar ainda o drag-and-drop — implementar o **que sustenta** o drag-and-drop.

> Fazer agora evita refatorar a camada de importação quando chegar Pierre, Gemini e Open Finance.
> Após esta fase, qualquer nova fonte conecta à mesma infraestrutura sem reescrever nada.

Fluxo atual:

```
CSV → Parser → Banco
```

Fluxo após esta fase:

```
CSV
 └─ Import Run (rastreado)
     └─ Artifact (arquivo preservado)
         └─ Parser
             └─ Staging (validação antes de commitar)
                 └─ Banco
```

Fluxo futuro — mesma infraestrutura, `source_type` diferente:

```
MyProfit / Pierre / Gemini / Open Finance / YFinance
 └─ Import Run (source_type = MYPROFIT | PIERRE | GEMINI | OPEN_FINANCE | YFINANCE)
     └─ mesma pipeline
```

### Tabela `import_runs`

Registrar metadados de cada importação realizada.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único do run |
| `source_type` | enum | `MYPROFIT`, `PIERRE`, `GEMINI`, `OPEN_FINANCE`, `YFINANCE`, `MANUAL` |
| `file_name` | string | Nome original do arquivo |
| `checksum` | string | SHA-256 do arquivo — impede re-importação duplicada |
| `started_at` | timestamp | Início do processamento |
| `finished_at` | timestamp | Fim do processamento |
| `status` | enum | `PENDING`, `PROCESSING`, `SUCCESS`, `PARTIAL`, `FAILED` |
| `rows_read` | int | Total de linhas lidas |
| `rows_inserted` | int | Linhas inseridas com sucesso |
| `rows_updated` | int | Linhas atualizadas |
| `rows_failed` | int | Linhas rejeitadas |
| `error_log` | JSON | Erros detalhados por linha |
| `created_by` | string | Usuário que iniciou a importação |

- ✅ Criar tabela `import_runs` com os campos acima
- ✅ Verificação de checksum antes de processar — rejeitar arquivo já importado com aviso claro
- ✅ Status `PARTIAL` quando parte das linhas falha — não bloquear importação inteira por erros isolados

### Tabela `import_artifacts`

Preservar referência ao arquivo original para reprocessamento futuro e auditoria.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único |
| `import_run_id` | UUID | FK para `import_runs` |
| `artifact_type` | enum | `PROVENTO_CSV`, `EVOLUCAO_CSV`, `TABLE_EXPORT_CSV`, `PIERRE_MSG`, `GEMINI_JSON` |
| `storage_path` | string | Caminho no filesystem ou object storage |
| `sha256` | string | Hash do arquivo armazenado |
| `size_bytes` | int | Tamanho em bytes |
| `created_at` | timestamp | Data de armazenamento |

- ✅ Criar tabela `import_artifacts`
- ✅ Salvar cópia do arquivo original em `archive/imports/YYYY-MM/` antes de processar
- ✅ Botão "Reprocessar" na tela de histórico — reprocessa sem novo upload (usa artifact salvo)

### Tabela `prompt_versions`

Versionar os prompts da IA para rastrear qualidade ao longo do tempo.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único |
| `name` | string | Ex: `prompt_pix`, `prompt_cartao`, `prompt_myprofit_dividendos` |
| `version` | int | Versão incremental: 1, 2, 3… |
| `content` | text | Corpo completo do prompt |
| `active` | bool | Apenas um ativo por `name` por vez |
| `created_at` | timestamp | Data de criação |
| `notes` | text | O que mudou em relação à versão anterior |

- ✅ Criar tabela `prompt_versions`
- ✅ Seeds iniciais: `prompt_pix_v1`, `prompt_cartao_v1`, `prompt_fatura_v1`, `prompt_extrato_v1`
- ✅ Endpoint para ativar/desativar versão de prompt sem necessidade de deploy

### Tabela `ai_runs`

Histórico de cada chamada à IA para debug, análise de qualidade e geração de few-shots.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único |
| `import_run_id` | UUID | FK para `import_runs` (opcional) |
| `prompt_version_id` | UUID | FK para `prompt_versions` |
| `model` | string | Ex: `gemini-1.5-pro` |
| `input_text` | text | Mensagem original enviada à IA |
| `output_json` | JSON | Resposta estruturada retornada |
| `confidence` | float | Score de confiança retornado pelo modelo |
| `latency_ms` | int | Tempo de resposta em ms |
| `status` | enum | `SUCCESS`, `FAILED`, `LOW_CONFIDENCE` |
| `created_at` | timestamp | Data da chamada |

- ✅ Criar tabela `ai_runs`
- ✅ Salvar todos os runs independente de sucesso ou falha
- ⬜ Painel simples de qualidade: confiança média por `prompt_version` ao longo do tempo

### Migração de arquivos fundadores para `archive/bootstrap-data/`

Os arquivos CSV originais têm valor permanente como fixtures oficiais — teste, benchmark e regressão.

- ✅ Mover para `archive/bootstrap-data/`:
  - `data/raw/myprofit/` → `archive/bootstrap-data/myprofit/`
  - `data/raw/nubank/` → `archive/bootstrap-data/nubank/`
  - `Extrato_Pierre_Auditado.csv` → `archive/bootstrap-data/pierre/`
- ✅ Adicionar `README.md` em `archive/bootstrap-data/` explicando origem e uso de cada arquivo
- ⬜ Usar esses arquivos como fixtures em testes de parser (regressão automática)
- ✅ Regra: nunca deletar ou modificar arquivos nesta pasta — são a fonte da verdade histórica

---

## ✅ Fase 1 — Importação MyProfit

**Objetivo:** interface de upload que usa a infraestrutura criada na Fase 0.5.

> Depende da Fase 0.5 — `import_runs` e `import_artifacts` devem existir antes do drag-and-drop.

- ✅ Página definitiva de importação com drag and drop
- ✅ Instrução contextual por tipo de arquivo (exibir antes do upload)
- ✅ Pré-validação de colunas antes de processar — rejeitar com lista clara das colunas ausentes
- ✅ Preview dos dados antes de confirmar importação
- ✅ Relatório pós-importação usando dados de `import_runs` (inseridos / atualizados / falhos)
- ✅ Histórico de importações: tabela listando `import_runs` com status e botão Reprocessar

### Provento.csv

- ✅ Colunas padrão do MyProfit — sem seleção extra pelo usuário
- ✅ Instrução: apenas confirmar nome do arquivo

### tableExport.csv (posições da carteira)

- ✅ Colunas padrão — sem seleção extra pelo usuário
- ✅ Instrução: apenas confirmar nome do arquivo

### Evolucao_Carteira.csv

> ⚠️ Este arquivo exige seleção manual de colunas no MyProfit antes do download.
> Exibir a tabela abaixo como instrução contextual antes do upload.

Colunas obrigatórias a selecionar no MyProfit (20 colunas):

| Grupo | Colunas |
|---|---|
| Base | Data · % Mensal · % Acumulada · Patrimônio · Compras · Vendas · Op. Finalizadas · Proventos |
| IBOV | IBOV Mensal · IBOV Acumulado |
| CDI | CDI Mensal · CDI Acumulado |
| IPCA | IPCA Mensal · IPCA Acumulado |
| IFIX | IFIX Mensal · IFIX Acumulado |
| S&P 500 | S&P Mensal · S&P Acumulado |
| IDIV | IDIV Mensal · IDIV Acumulado |

- ✅ Validar presença das 20 colunas — rejeitar com lista das colunas ausentes se faltar alguma
- ✅ Instrução inline com a tabela acima antes do campo de upload

---

## ✅ Fase 2 — Administração do banco

**Objetivo:** permitir correção manual de dados pelo admin sem acessar o banco diretamente.

- ✅ Infraestrutura de Governança concluída
- ✅ Auditoria (tabela nativa `audit_log` e histórico visual) concluída
- ✅ CRUD Administrativo de Transações concluído (edição visual com logs automáticos)
- ✅ APIs Administrativas de Posições, Dividendos e Categorias concluídas
- ✅ Navegação na governança e componentes reutilizáveis de administração em pé

---

## 🔄 Fase 3 — Governança dos dados 🆕

**Objetivo:** criar a camada de confiança (curadoria visual). Dados confiáveis são pré-requisito para Metas e IA.

Transformar as APIs administrativas já existentes em ferramentas visuais de curadoria de dados:

- ⬜ CRUD visual de Posições
- ⬜ CRUD visual de Dividendos
- ⬜ Merge de Categorias
- ⬜ Reclassificação de Ativos
- ⬜ Correção de Tickers
- ⬜ Ferramentas de Saneamento
- ⬜ Consistência e Qualidade dos Dados
- ⬜ Painéis avançados de Governança
- ⬜ Regras de validação de entrada por tipo de lançamento (PIX, cartão, TED, boleto)
- ⬜ Detecção de duplicatas na importação (mesmo valor + data + descrição)
- ⬜ Score de qualidade dos dados por mês (% de transações sem categoria, sem valor, etc.)
- ⬜ Painel de saúde dos dados — alertas visuais para inconsistências detectadas
- ⬜ Dataset de correções do usuário para few-shots na IA:
  - Cada correção manual salva um par (entrada original → categoria correta)
  - Após N correções, gerar arquivo de few-shots automaticamente
  - Alimentar chamadas futuras ao Gemini (ver Fase 8)

---

## ⬜ Fase 4 — MVP Stabilization 🆕

**Objetivo:** estabilizar a base antes de espalhar dependências com o módulo Metas.

- ⬜ Resolver todos os warnings do React (chaves únicas, deps de useEffect, etc.)
- ⬜ Revisar e eliminar hooks duplicados entre módulos
- ⬜ Revisar componentes duplicados (Wealth vs Dashboard)
- ⬜ Eliminar tipagens `any` remanescentes — substituir por tipos concretos
- ⬜ Remover `console.log` esquecidos
- ⬜ Resolver todos os `TODO` e `FIXME` no código
- ⬜ Remover imports mortos
- ⬜ Revisar queries lentas — adicionar índices onde necessário
- ⬜ Revisar cache — evitar re-fetch desnecessário ao trocar de aba
- ⬜ Revisar estados globais — garantir consistência entre módulos
- ⬜ Review de performance dos gráficos — avaliar memoização e downsampling de séries longas

---

## ⬜ Fase 5 — Backup e Restore

**Objetivo:** garantir que nenhum dado seja perdido antes de qualquer deploy ou migração.

> Fazer antes do Docker. Patrimônio, dividendos e histórico real não podem ser perdidos
> em uma migração ou erro de ambiente.

- ⬜ Exportar banco completo em JSON
- ⬜ Exportar banco em SQLite
- ⬜ Importar backup de volta (restore completo)
- ⬜ Backup incremental (só o que mudou desde o último backup)
- ⬜ Verificação de integridade pós-restore

---

## ⬜ Fase 6 — Docker e documentação

- ⬜ Dockerfile frontend (Next.js, multi-stage build)
- ⬜ Dockerfile backend
- ⬜ `docker-compose.yml` completo (frontend + backend + banco + volumes persistentes)
- ⬜ `.env.example` documentado com todas as variáveis necessárias
- ⬜ README com setup em 3 passos: clone → `docker-compose up` → abrir localhost
- ⬜ Documentação de arquitetura (fluxo de dados, estrutura de pastas, decisões técnicas)
- ⬜ Documentação do módulo Wealth (endpoints, shapes de response, cálculo de alpha e DY)
- ⬜ Documentação dos importadores (colunas por CSV, configuração do pipeline Gemini)
- ⬜ CI/CD com GitHub Actions: lint → testes → build (bloquear merge se falhar)

---

## ⬜ Fase 7 — Metas financeiras

**Objetivo:** fechar o ciclo — transformar o sistema de painel de consulta em ferramenta de decisão.

> Depende de: Importação estável (Fase 1) + Governança dos dados (Fase 3) + MVP Stabilization (Fase 4).

- ⬜ Estrutura de dados: tabela `goals` (tipo, valor_alvo, prazo, status, progresso)
  - Tipos: `reserva_emergencia`, `viagem`, `imovel`, `independencia_financeira`, `livre`
- ⬜ Integração com Controle Financeiro — saldo mensal médio e sobra média
- ⬜ Integração com Wealth — patrimônio, rentabilidade e dividendos como contribuição às metas
- ⬜ Simulador de cenários: conservador (saldo atual) vs otimista (aumento de aportes/rentabilidade)
- 🆕 Simulador de aportes: "Se eu aportar R$X/mês, quando chego a R$Y?" — rentabilidade histórica real
- 🆕 Recomendação de onde aportar: score de diversificação atual → sugerir classe (pré-YFinance: lógica local)

---

## ⬜ Fase 8 — Automação com Gemini API

**Objetivo:** eliminar o processo manual de Pierre → cópia → Gemini → ajuste → importação.

> As tabelas `prompt_versions` e `ai_runs` criadas na Fase 0.5 são usadas aqui diretamente.

- ⬜ Integração `python-genai` (googleapis/python-genai)
- ⬜ Pipeline: mensagem Pierre → Gemini → JSON estruturado → importação automática via `import_runs`
- ⬜ Classificação automática: PIX, cartão, TED, boleto → categoria sugerida + grau de confiança
- 🆕 Ativar prompts da biblioteca (seeds criados na Fase 0.5) como base inicial
- 🆕 Aplicar técnicas de prompt engineering (few-shot, chain-of-thought, output JSON estruturado)
  - Referência: https://www.promptingguide.ai/pt
- 🆕 Alimentar few-shots automaticamente com o dataset de correções da Fase 3

---

## ⬜ Fase 9 — Market Data / YFinance 🆕

**Objetivo:** abstrair o provider de dados de mercado para evitar reescrita futura ao trocar de fonte.

> Implementar camada de abstração antes de usar YFinance diretamente.

Arquitetura:

```
App
 └─ MarketDataService (adapter)
     ├─ YFinance       ← implementar primeiro
     ├─ BrAPI          ← fallback para ativos BR
     ├─ AlphaVantage   ← futuro
     └─ Polygon        ← futuro
```

- ⬜ Criar `MarketDataService` com interface padronizada (preço, DY, valuation)
- ⬜ Implementar adapter YFinance
- ⬜ Recomendações de rebalanceamento (detectar excesso por classe: ações, FIIs, caixa)
- ⬜ Radar de oportunidades: ações com DY alto, FIIs descontados, ativos abaixo do preço médio
- 🆕 Alertas de oportunidade (Telegram ou e-mail) quando ativo atingir condição definida pelo usuário

---

## ⬜ Fase 10 — Central de Insights 🆕

**Objetivo:** superfície unificada que aproveita tudo já construído e entrega inteligência sem esforço.

Exemplos de insights automáticos:

```
• Seu patrimônio cresceu 4,2% no mês
• Dividendos aumentaram 17% vs ano anterior
• Sua exposição a FIIs caiu abaixo da meta de alocação
• Você gastou 32% mais com alimentação este mês
• Você está 5 meses adiantado na Meta FIRE
• 3 ativos da carteira estão abaixo do preço médio de compra
```

- ⬜ Engine de insights: regras configuráveis por módulo (Controle Financeiro, Wealth, Metas)
- ⬜ Página Central de Insights com feed cronológico
- ⬜ Insights fixados (marcados como importantes pelo usuário)
- ⬜ Notificações internas para insights de alta relevância

---

## ⬜ Fase 11 — Segurança e testes

**Objetivo:** preparar para uso contínuo e eventual exposição além do localhost.

- ⬜ Auditoria de segurança do código gerado por IA:
  - SQL Injection em todas as queries dinâmicas
  - XSS em inputs e renderização de dados externos
  - SSRF em integrações com APIs externas (Gemini, YFinance, Open Finance)
  - Revisão de autenticação e autorização em todos os endpoints
- ⬜ Eliminar duplicações remanescentes pós-Stabilization
- ⬜ Testes unitários: hooks e utilitários (Jest ou Vitest)
- ⬜ Testes de integração: APIs principais (happy path + cenários de erro)
- ⬜ Testes E2E com Playwright: fluxos críticos (importação, classificação, visualização de patrimônio)
- ⬜ Usar arquivos de `archive/bootstrap-data/` como fixtures nos testes de parser

---

## ⬜ Fase 12 — MVP profissional

- ⬜ Aba Configurações: tema, moeda, parâmetros de importação
- ⬜ Aba Perfil: nome, patrimônio alvo, perfil de investidor (base para personalização de metas)

---

## 🔮 Backlog futuro

Sem prazo definido. Entram no roadmap quando houver demanda real.

| Item | Observação |
|---|---|
| Open Finance (Pluggy / Belvo / Quanto) | Substituiria importação manual. A infraestrutura `import_runs` já suporta `source_type = OPEN_FINANCE` |
| Conciliação bancária automática | Depende de Open Finance |
| App Mobile / PWA offline | |
| Multiusuário e compartilhamento familiar | |
| IA conversacional financeira | Chat com contexto da carteira e histórico |
| Integração B3 / CEI automática | |
| Score financeiro próprio | |
| Planejamento FIRE + simulador de aposentadoria | |
| Relatório IRPF automatizado | |
| Alertas por Telegram / WhatsApp | Versão simples pode vir na Fase 9 |
| Machine Learning de classificação | Após dataset de correções ser grande o suficiente |

---

## Dependências entre fases

```
Fase 0 (Polish) ✅
    └─ Fase 0.5 (Governança de Importação)   ← NOVO: fundação de tudo
        └─ Fase 1 (Importação CSV)
            └─ Fase 2 (Administração do banco)
                └─ Fase 3 (Governança dos dados)
                    └─ Fase 4 (MVP Stabilization)
                        ├─ Fase 5 (Backup e Restore)
                        │   └─ Fase 6 (Docker + Docs)
                        └─ Fase 7 (Metas)
                            └─ Fase 8 (Gemini)       ← usa prompt_versions e ai_runs da 0.5
                                └─ Fase 9 (Market Data)
                                    └─ Fase 10 (Central de Insights)
                                        └─ Fase 11 (Segurança e Testes)
                                            └─ Fase 12 (MVP)
```

---

*Última atualização: junho de 2026*