import os

markdown_content = """# FRONTEND INVENTORY FREEZE - FASE 10A

Documentação gerada via engenharia reversa do frontend da aplicação Fin Analytics V2.
Nenhuma suposição foi feita; todas as informações foram extraídas diretamente dos arquivos fonte.

---

## 1. PÁGINAS (PAGES)

| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/app/page.tsx` | Ponto de entrada do Dashboard principal. | Renderiza o DashboardPage e gerencia a visualização raiz. |
| `src/app/subscriptions/page.tsx` | Visualização de assinaturas (subscriptions). | Exibe dados de inscrições, pacotes e gastos recorrentes. |
| `src/app/transactions/page.tsx` | Visualização de transações. | Apresenta a lista de transações e filtros para navegação de dados transacionais. |
| `src/app/wealth/page.tsx` | Visão geral de patrimônio (Wealth). | Ponto central de informações de patrimônio e investimentos. |
| `src/app/wealth/allocation/page.tsx` | Página detalhada de alocação de ativos. | Exibe gráficos e tabelas sobre a distribuição de portfólio. |
| `src/app/wealth/asset/[ticker]/page.tsx` | Página dinâmica de ativo específico. | Apresenta histórico, performance e detalhes de um ativo específico (ticker). |
| `src/app/wealth/dividends/page.tsx` | Página de visualização de dividendos. | Demonstra fluxo e comparativos anuais de proventos. |
| `src/app/wealth/evolution/page.tsx` | Página de evolução patrimonial. | Demonstração do crescimento do portfólio ao longo do tempo. |
| `src/app/wealth/patrimonio/page.tsx` | Página de evolução de patrimônio líquido. | Acompanhamento do patrimônio total consolidado. |

---

## 2. LAYOUTS

| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/app/layout.tsx` | Layout raiz da aplicação (RootLayout). | Configuração global, injeção de fontes, e provedores de contexto na árvore de componentes. |
| `src/app/wealth/layout.tsx` | Layout do módulo de Wealth. | Renderização da estrutura de navegação e período específicos para views de patrimônio. |

---

## 3. COMPONENTES

### 3.1. Layout & Estrutura
| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/components/layout/AppShell.tsx` | Casca (shell) principal da aplicação. | Estruturação de menus laterais, topo e área de conteúdo principal. |
| `src/components/layout/PageLayout.tsx` | Wrapper padrão para páginas. | Mantém o padrão de espaçamento, padding e alinhamento de conteúdo. |
| `src/components/layout/TopNav.tsx` | Barra de navegação superior. | Navegação principal, exibição de usuário e ações globais de cabeçalho. |

### 3.2. Dashboard (Cards & Views)
| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/components/dashboard/DashboardPage.tsx` | Agregador de componentes do dashboard. | Montagem da tela inicial com os componentes visuais principais. |
| `src/components/dashboard/SummaryCards.tsx` | Exibição de cards de resumo. | Apresenta KPIs como saldo, receita e despesa agregados. |
| `src/components/dashboard/CategoriesCard.tsx` | Visualização resumida de categorias. | Mostra as despesas/receitas agrupadas por categoria. |
| `src/components/dashboard/InstallmentCard.tsx` | Resumo de parcelamentos. | Mostra o impacto de parcelamentos e assinaturas. |
| `src/components/dashboard/PacingCard.tsx` | Card de acompanhamento de ritmo (pacing). | Medição do ritmo de gastos versus orçamento ou tempo no mês. |
| `src/components/dashboard/AllocationChart.tsx` | Gráfico de alocação inicial. | Demonstração gráfica da divisão de recursos no dashboard. |

### 3.3. Wealth (Gráficos, Tabelas e Cards)
| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/components/wealth/charts/AdvancedAlphaChart.tsx` | Gráfico avançado de Alpha. | Compara a performance do portfólio contra benchmarks, demonstrando evolução e pontos de inflexão. |
| `src/components/wealth/charts/AllocationDonut.tsx` | Gráfico de rosca de alocação. | Exibe a proporção percentual de diferentes ativos ou classes no portfólio. |
| `src/components/wealth/charts/AllocationTreemap.tsx` | Mapa de árvore de alocação. | Visualização hierárquica e proporções de ativos na carteira. |
| `src/components/wealth/charts/AssetHistoryChart.tsx` | Gráfico de histórico de ativo. | Demonstração do preço, variações e volume histórico de um ticker específico. |
| `src/components/wealth/charts/CashflowBarChart.tsx` | Gráfico de barras de fluxo de caixa. | Exibe entradas e saídas de caixa periodizadas. |
| `src/components/wealth/charts/DiversificationGauge.tsx` | Gráfico de ponteiro de diversificação. | Mede e exibe visualmente uma nota ou índice de diversificação da carteira. |
| `src/components/wealth/charts/DividendFlowChart.tsx` | Gráfico de fluxo de dividendos. | Visualização em barras/linhas de proventos recebidos ao longo do tempo. |
| `src/components/wealth/charts/DividendYoYChart.tsx` | Gráfico Year-Over-Year de dividendos. | Compara o recebimento de dividendos de um ano contra anos anteriores no mesmo período. |
| `src/components/wealth/charts/GrowthComposedChart.tsx` | Gráfico composto de crescimento. | Mostra a evolução patrimonial usando áreas e barras, combinando crescimento orgânico e aportes. |
| `src/components/wealth/ui/WealthChartCard.tsx` | Card contêiner para gráficos. | Prover encapsulamento, título, bordas e botões de atualização/aviso para gráficos Recharts. |
| `src/components/wealth/ui/WealthKpiCard.tsx` | Card para KPIs de wealth. | Renderizar indicadores chave (ex: Patrimônio, Rentabilidade) com ícones e valores de variação. |
| `src/components/wealth/ui/WealthPeriodToggle.tsx` | Botões de alternância de período. | Permitir seleção de filtro temporal (ex: YTD, 1Y, Todos) para gráficos e tabelas. |
| `src/components/wealth/ui/WealthSectionTitle.tsx` | Título padronizado de seções. | Exibe cabeçalhos textuais consistentes para divisões dentro de Wealth. |
| `src/components/wealth/ui/WealthTable.tsx` | Tabela genérica para dados de patrimônio. | Listagem, paginação e visualização em grade de dados financeiros e posições. |
| `src/components/wealth/ui/WealthTooltip.tsx` | Tooltip customizado para Recharts. | Prover informações formatadas (moedas, datas) ao passar o mouse sobre gráficos. |

### 3.4. Governança
| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/components/governance/DataTabsNav.tsx` | Navegação em abas para Governança. | Alternar visualização entre diferentes tipos de dados e tabelas (Tabs). |
| `src/components/governance/CategoriesTab.tsx` | Aba de Categorias. | Listar categorias financeiras permitindo interações de gestão. |
| `src/components/governance/DividendsTab.tsx` | Aba de Dividendos. | Exibir tabela de registros de dividendos da área de governança. |
| `src/components/governance/PositionsTab.tsx` | Aba de Posições (Ativos). | Mostrar o detalhamento de posições abertas ou fechadas de ativos. |
| `src/components/governance/TransactionsTab.tsx` | Aba de Transações. | Listar transações gerais cadastradas no sistema. |

### 3.5. Administração (Modais e Tabelas)
| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/components/admin/AdminEditDialog.tsx` | Modal genérico de edição. | Permitir a inserção/alteração de entidades pelo administrador. |
| `src/components/admin/AdminFilters.tsx` | Filtros para listagens admin. | Componentes de busca, datas e drop-downs para filtrar tabelas. |
| `src/components/admin/AdminPagination.tsx` | Controle de paginação. | Botões e indicadores de próxima página/página anterior para listagens. |
| `src/components/admin/AdminTable.tsx` | Tabela padronizada de admin. | Grid reutilizável para renderizar colunas dinâmicas e dados estruturados. |
| `src/components/admin/CategoryMergeDialog.tsx` | Modal de fusão de categorias. | Ação específica de unificar duas ou mais categorias de despesa/receita. |
| `src/components/admin/DividendEditDialog.tsx` | Modal de edição de dividendos. | Formulario de alteração de dados de proventos recebidos. |
| `src/components/admin/PositionEditDialog.tsx` | Modal de edição de posições. | Formulário para corrigir número de cotas, preço médio e valores de posições. |
| `src/components/admin/TransactionEditDialog.tsx` | Modal de edição de transação. | Interface para ajustar valores, datas e descrições de lançamentos individuais. |

### 3.6. UI (Genéricos / Core)
| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/components/ui/button.tsx` | Elemento primitivo de Botão. | Botão reusável baseado em variantes de design (ex: tamanho, cor). |
| `src/components/ui/DeltaBadge.tsx` | Badge de variação. | Indica crescimento ou queda com cores e setas formatadas visualmente. |
| `src/components/ui/PillTabs.tsx` | Abas no formato "Pill". | Navegação horizontal com botões de seleção de abas de formato arredondado. |
| `src/components/ui/AuthRequiredCard.tsx` | Card de restrição. | Interface para informar que a área necessita de login ou nível de acesso específico. |

### 3.7. Provedores
| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/components/providers/RechartsConsoleWarningFix.tsx` | Correção/Silenciador de warnings do Recharts. | Intercepta o console log do navegador para ignorar avisos visuais de compatibilidade de bibliotecas. |

---

## 4. HOOKS

| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/hooks/useAdminCRUD.ts` | Operações CRUD Genéricas / Admin. | Provê métodos para Criação, Leitura, Atualização e Deleção para tabelas no contexto admin. |
| `src/hooks/useAllocationData.ts` | Obtenção de dados de alocação. | Conecta ao backend/store para buscar `AssetAllocation` e `PositionDetail`. |
| `src/hooks/useAlphaData.ts` | Obtenção de dados de rentabilidade (Alpha). | Processa pontos de evolução e performance sobre tempo. |
| `src/hooks/useAudit.ts` | Interação com dados de Auditoria. | Consulta execuções (runs) e gerencia requests de rollback (AuditRollback). |
| `src/hooks/useCategoriesAdmin.ts` | Hook de administração de categorias. | Paginação, filtros e lista de Categorias. |
| `src/hooks/useCurrentUser.ts` | Obtenção de usuário logado. | Retorna os dados do contexto de autenticação do usuário. |
| `src/hooks/useDatabaseAdmin.ts` | Ferramentas administrativas do Banco de Dados. | Extração de sumário do DB, integridade, status de tabelas e estimativas de vacuum (limpeza). |
| `src/hooks/useDividendsAdmin.ts` | Hook de administração de dividendos. | Busca, filtragem e paginação da listagem de dividendos para o admin. |
| `src/hooks/useDividendsData.ts` | Fetch e processamento analítico de dividendos. | Entrega histórico, quebra e evolução dos dividendos recebidos no portfólio. |
| `src/hooks/useGrowthData.ts` | Busca de evolução de crescimento do portfólio. | Retorna sumários e pontos de evolução patrimonial calculados no tempo. |
| `src/hooks/usePositionsAdmin.ts` | Hook de administração de posições. | Trata busca e filtros das posições abertas para interface de governança. |
| `src/hooks/useTransactions.ts` | Busca de dados transacionais. | Controla filtros complexos e paginação do ledger (livro-razão) de transações. |
| `src/hooks/useWealthStore.ts` | Consumo de estado global de Wealth. | Acesso facilitado às variáveis de estado armazenadas via Zustand para módulos de patrimônio. |

---

## 5. STORES

| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/store/` (Pasta identificada mapeada via `useWealthStore.ts`) | Gerenciamento de estado global. | Responsável por manter variáveis de memória compartilhadas entre componentes (ex: período selecionado, filtros globais). |

---

## 6. CONTEXTS

| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/contexts/AuthContext.tsx` | Provedor de contexto de Autenticação. | Mantém o estado global do login do usuário e compartilha tokens ou informações de sessão com toda a árvore do React. |

---

## 7. LIB / CONFIG / TYPES

| Arquivo | Responsabilidade | Funcionalidades Atendidas |
|---------|-----------------|---------------------------|
| `src/lib/api.ts` | Funções de conexão API. | Tratamento de requisições base, fetch, validação e mapeamento de `AuthError`. |
| `src/lib/colors.ts` | Paleta e Identidade visual em código. | Prover dicionários de cor de categorias (`CATEGORY_COLORS`), identidades de ativos e cálculos de cor semântica. |
| `src/lib/period.ts` | Utilidades de processamento temporal. | Resolução de mês, formatação de rotulagens e cálculos de ranges de datas (ex: limites de mês). |
| `src/lib/utils.ts` | Utilitários core. | Composição de classes (`cn`), formatação monetária (`formatCurrency`) e resolução de cores baseada em score. |
| `src/config/navigation.ts` | Regras de roteamento e menus. | Definição das constantes `SIDEBAR_NAV`, `SECTION_TABS` e funções para reconstruir parâmetros de busca. |
| `src/types/api.ts` | Tipagem de APIs. | Define interfaces padrão para chamadas de API (`APIError`). |
| `src/types/dto.ts` | Objetos de Transferência de Dados. | Declara payloads para API como `UpdateTransactionDTO`, `PaginatedResponse`, etc. |
| `src/types/entities.ts` | Modelos de Domínio no Frontend. | Tipagem exata das entidades do negócio (`Transaction`, `Position`, `Dividend`, `Category`, `PortfolioEvolution`, etc). |
"""

with open(r"C:\Users\Cleidson\Pictures\fin_analytics_v2\FRONTEND_INVENTORY.md", "w", encoding="utf-8") as f:
    f.write(markdown_content)
