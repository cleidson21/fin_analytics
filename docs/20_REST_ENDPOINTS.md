> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Endpoints REST (Pierre Finance) [EXTRAÍDOS DO OPENAPI]

## GET /tools/api/get-bills
- **Summary:** [PENDENTE]
- **Description:** Retorna faturas de cartão de crédito vencidas (apenas faturas já fechadas e com vencimento passado) do usuário autenticado. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** getBills
- **Parameters:**
  - `accountId` (query): Opcional - ID da conta de cartão de crédito para filtrar as faturas (opcional)
- **Responses:**
  - `200`: Lista de faturas de cartão de crédito vencidas
  - `401`: 
  - `500`: 

## GET /tools/api/get-bill-summary
- **Summary:** [PENDENTE]
- **Description:** Retorna o resumo da fatura atual do(s) cartão(ões) de crédito do usuário: limite total, limite disponível, período considerado e o valor aproximado da fatura. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** getBillSummary
- **Parameters:**
  - `accountId` (query): Opcional - ID da conta de cartão de crédito para filtrar o cálculo (opcional)
  - `closingDay` (query): Opcional - Dia de fechamento manual (1–31). Se informado junto com accountId, será usado no cálculo deste cartão.
  - `startDate` (query): Opcional - Data de início do período para cálculo da fatura (formato ISO 8601). Sobrescreve o cálculo automático baseado no closing day.
  - `endDate` (query): Opcional - Data de fim do período para cálculo da fatura (formato ISO 8601). Sobrescreve o cálculo automático baseado no closing day.
- **Responses:**
  - `200`: Resumo da fatura corrente
  - `401`: 
  - `500`: 

## POST /tools/api/manage-closing-date
- **Summary:** [PENDENTE]
- **Description:** Gerencia datas de fechamento de cartões de crédito. Permite listar contas, criar, atualizar, deletar e consultar datas de fechamento. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** manageClosingDate
- **Parameters:** Nenhum
- **Body:** [CONFIRMADO] Requer payload.
- **Responses:**
  - `200`: Operação realizada com sucesso
  - `400`: Parâmetros inválidos
  - `401`: 
  - `403`: Acesso negado
  - `404`: Recurso não encontrado
  - `500`: 

## GET /tools/api/get-api-key-info
- **Summary:** [PENDENTE]
- **Description:** Get information about how to generate and use API keys for Pierre Finance
- **Operation ID:** getApiKeyInfo
- **Parameters:** Nenhum
- **Responses:**
  - `200`: API key information and available tools
  - `500`: Internal server error

## GET /tools/api/get-accounts
- **Summary:** [PENDENTE]
- **Description:** Retorna todas as contas financeiras do usuário. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** getAccounts
- **Parameters:** Nenhum
- **Responses:**
  - `200`: Lista de contas financeiras
  - `401`: Authentication or subscription error
  - `500`: Internal server error

## GET /tools/api/get-balance
- **Summary:** [PENDENTE]
- **Description:** Retorna o saldo total e detalhes de todas as contas bancárias. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** getBalance
- **Parameters:** Nenhum
- **Responses:**
  - `200`: Dados de saldo consolidado
  - `401`: Authentication or subscription error
  - `500`: Internal server error

## GET /tools/api/get-balance-by-account
- **Summary:** [PENDENTE]
- **Description:** Retorna o saldo e detalhes de uma conta bancária específica. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** getBalanceByAccount
- **Parameters:**
  - `accountId` (query): Obrigatório - Identificador único da conta bancária
- **Responses:**
  - `200`: Dados de saldo da conta
  - `400`: Parâmetros inválidos
  - `401`: Authentication or subscription error
  - `404`: Conta não encontrada
  - `500`: Erro interno do servidor

## GET /tools/api/get-installments
- **Summary:** [PENDENTE]
- **Description:** Retrieve all installments transactions of the period. Fetches ALL installments (past, current, and future) for purchases made within the specified period. Requires API key for authentication and active subscription.
- **Operation ID:** getInstallments
- **Parameters:**
  - `startDate` (query): Opcional - Start date for filtering. Defaults to first day 3 months ago if not provided.
  - `endDate` (query): Opcional - End date for filtering. Defaults to last day of current month if not provided.
- **Responses:**
  - `200`: Installments data and statistics
  - `401`: Authentication or subscription error
  - `500`: Internal server error

## GET /tools/api/get-transactions
- **Summary:** [PENDENTE]
- **Description:** Retrieves the user's financial transaction history within a specific period with intelligent filtering and automatic categorization. Supports filtering by account type, transaction type, category, amount ranges, and natural language queries via clientMessage parameter. Applies two processing stages: 1) LLM-powered intelligent filtering (when clientMessage is provided), 2) Automatic transaction categorization (always applied). Supports two response formats: 'raw' (default) for unprocessed data, and 'structured' for organized data with groupings and summaries. Requires API key for authentication and active subscription.
- **Operation ID:** getTransactions
- **Parameters:**
  - `startDate` (query): Opcional - Start date for filtering
  - `endDate` (query): Opcional - End date for filtering
  - `categories` (query): Opcional - Categories to filter by (comma-separated)
  - `minAmount` (query): Opcional - Minimum amount to filter by
  - `maxAmount` (query): Opcional - Maximum amount to filter by
  - `accountType` (query): Opcional - Account type to filter by
  - `accountSubtype` (query): Opcional - Account subtype to filter by
  - `includeStatus` (query): Opcional - Transaction statuses to include (comma-separated)
  - `format` (query): Opcional - Response format type (default: raw)
  - `clientMessage` (query): Opcional - Intelligent filter message for LLM-powered transaction filtering
- **Responses:**
  - `200`: List of transactions (format depends on 'format' parameter)
  - `400`: Invalid parameters
  - `401`: 
  - `500`: 

## POST /tools/api/manual-update
- **Summary:** [PENDENTE]
- **Description:** Synchronizes all connected financial accounts and transactions with the latest data from banks and credit card providers. Requires API key for authentication and active subscription.
- **Operation ID:** manualUpdate
- **Parameters:** Nenhum
- **Responses:**
  - `200`: Manual sync initiated
  - `400`: Sem contas conectadas encontradas
  - `401`: 
  - `500`: 

## POST /tools/api/create-spending-limit
- **Summary:** [PENDENTE]
- **Description:** Cria um novo limite de gastos personalizado para uma categoria específica. Requer API key para autenticação e assinatura ativa. O usuário deve ter cota disponível baseada no seu plano (Basic: 0 limites, Pro: 2 limites, Premium: 5 limites).
- **Operation ID:** createSpendingLimit
- **Parameters:** Nenhum
- **Body:** [CONFIRMADO] Requer payload.
- **Responses:**
  - `200`: Limite de gastos criado com sucesso
  - `400`: Parâmetros inválidos
  - `401`: 
  - `403`: Cota de limites excedida
  - `500`: 

## POST /tools/api/confirm-spending-limit
- **Summary:** [PENDENTE]
- **Description:** Confirma a criação de um limite de gastos após receber aviso sobre gastos atuais. Permite agendar o limite para o próximo período se necessário. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** confirmSpendingLimit
- **Parameters:** Nenhum
- **Body:** [CONFIRMADO] Requer payload.
- **Responses:**
  - `200`: Limite de gastos confirmado e criado
  - `400`: 
  - `401`: 
  - `403`: Cota de limites excedida
  - `500`: 

## GET /tools/api/list-spending-limits
- **Summary:** [PENDENTE]
- **Description:** Lista todos os limites de gastos do usuário com informações detalhadas de uso atual e validação automática de quota. Para cada limite, calcula automaticamente o valor gasto no período atual, porcentagem de uso, valor restante e status visual. Por padrão retorna apenas limites ativos, mas pode incluir inativos com o parâmetro includeInactive. SEMPRE verifica e retorna informações detalhadas sobre cota do plano (Basic: 0 alertas, Pro: 2 alertas, Premium: 5 alertas) incluindo mensagens formatadas de status e upgrade quando necessário. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** listSpendingLimits
- **Parameters:**
  - `includeInactive` (query): Opcional - Se deve incluir limites inativos na resposta
- **Responses:**
  - `200`: Lista de limites de gastos
  - `401`: 
  - `500`: 

## GET /tools/api/get-spending-limit-transactions
- **Summary:** [PENDENTE]
- **Description:** Retorna o status detalhado de um limite de gastos específico, incluindo valor gasto atual, porcentagem do limite, próximos alertas e histórico de transações. Calcula automaticamente o período baseado na configuração do limite. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** getSpendingLimitTransactions
- **Parameters:**
  - `limitId` (query): Obrigatório - ID do limite de gastos para consultar o status
- **Responses:**
  - `200`: Status detalhado do limite de gastos
  - `400`: Parâmetros inválidos
  - `401`: 
  - `403`: Acesso negado
  - `404`: Limite não encontrado
  - `500`: 

## PUT /tools/api/update-spending-limit
- **Summary:** [PENDENTE]
- **Description:** Atualiza um limite de gastos existente. Permite modificar categoria, valor, período e status ativo. O usuário só pode atualizar seus próprios limites. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** updateSpendingLimit
- **Parameters:** Nenhum
- **Body:** [CONFIRMADO] Requer payload.
- **Responses:**
  - `200`: Limite de gastos atualizado com sucesso
  - `400`: Parâmetros inválidos
  - `401`: 
  - `403`: Acesso negado
  - `404`: Limite não encontrado
  - `500`: 

## DELETE /tools/api/delete-spending-limit
- **Summary:** [PENDENTE]
- **Description:** Exclui permanentemente um limite de gastos. O usuário só pode excluir seus próprios limites. Esta operação não pode ser desfeita. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** deleteSpendingLimit
- **Parameters:** Nenhum
- **Body:** [CONFIRMADO] Requer payload.
- **Responses:**
  - `200`: Limite de gastos excluído com sucesso
  - `400`: Parâmetros inválidos
  - `401`: 
  - `403`: Acesso negado
  - `404`: Limite não encontrado
  - `500`: 

## POST /tools/api/create-payment-reminder
- **Summary:** [PENDENTE]
- **Description:** Cria um novo lembrete de pagamento. Permite criar lembretes únicos ou recorrentes com notificações via WhatsApp e Email. Requer API key para autenticação e assinatura ativa. O usuário deve ter cota disponível baseada no seu plano.
- **Operation ID:** createPaymentReminder
- **Parameters:** Nenhum
- **Body:** [CONFIRMADO] Requer payload.
- **Responses:**
  - `200`: Lembrete de pagamento criado com sucesso
  - `400`: Parâmetros inválidos
  - `401`: 
  - `403`: Cota de lembretes excedida
  - `500`: 

## GET /tools/api/list-payment-reminders
- **Summary:** [PENDENTE]
- **Description:** Lista todos os lembretes de pagamento do usuário com informações de cota. Permite filtrar por status (active, all, upcoming, overdue). Requer API key para autenticação e assinatura ativa.
- **Operation ID:** listPaymentReminders
- **Parameters:**
  - `filter` (query): Opcional - Filtro de lembretes: active (padrão), all, upcoming, overdue
  - `days` (query): Opcional - Número de dias para filtrar lembretes próximos (usado com filter=upcoming)
- **Responses:**
  - `200`: Lista de lembretes de pagamento
  - `401`: 
  - `500`: 

## PUT /tools/api/update-payment-reminder
- **Summary:** [PENDENTE]
- **Description:** Atualiza um lembrete de pagamento existente. Permite modificar título, valor, datas, padrão de recorrência e status. O usuário só pode atualizar seus próprios lembretes. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** updatePaymentReminder
- **Parameters:** Nenhum
- **Body:** [CONFIRMADO] Requer payload.
- **Responses:**
  - `200`: Lembrete de pagamento atualizado com sucesso
  - `400`: Parâmetros inválidos
  - `401`: 
  - `403`: Acesso negado
  - `404`: Lembrete não encontrado
  - `500`: 

## DELETE /tools/api/delete-payment-reminder
- **Summary:** [PENDENTE]
- **Description:** Exclui ou cancela um lembrete de pagamento. Por padrão realiza exclusão lógica (marca como inactive), mas pode fazer exclusão permanente com hardDelete=true. O usuário só pode excluir seus próprios lembretes. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** deletePaymentReminder
- **Parameters:**
  - `reminderId` (query): Obrigatório - ID do lembrete de pagamento a ser excluído
  - `hardDelete` (query): Opcional - Se deve fazer exclusão permanente (true) ou apenas cancelar (false, padrão)
- **Responses:**
  - `200`: Lembrete de pagamento excluído/cancelado com sucesso
  - `400`: Parâmetros inválidos
  - `401`: 
  - `403`: Acesso negado
  - `404`: Lembrete não encontrado
  - `500`: 

## GET /tools/api/get-expensive-categories
- **Summary:** [PENDENTE]
- **Description:** Retorna as 3 categorias mais caras no período especificado. Por padrão, analisa os últimos 7 dias. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** getExpensiveCategories
- **Parameters:**
  - `startDate` (query): Opcional - Data inicial para análise (formato YYYY-MM-DD). Padrão: 7 dias atrás.
  - `endDate` (query): Opcional - Data final para análise (formato YYYY-MM-DD). Padrão: hoje.
- **Responses:**
  - `200`: Top 3 categorias mais caras
  - `401`: 
  - `500`: 

## GET /tools/api/get-book
- **Summary:** [PENDENTE]
- **Description:** Obtém contexto financeiro e análises do usuário. Retorna informações consolidadas sobre contas, transações, saldos e categorias. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** getBook
- **Parameters:**
  - `includeAllPeriods` (query): Opcional - Se deve incluir dados de todos os períodos
  - `includeCreditCard` (query): Opcional - Se deve incluir informações de cartão de crédito
  - `includeCategories` (query): Opcional - Se deve incluir análise por categorias
- **Responses:**
  - `200`: Contexto financeiro do usuário
  - `401`: 
  - `500`: 

## GET /tools/api/get-memories
- **Summary:** [PENDENTE]
- **Description:** Adiciona uma mensagem do usuário (se fornecida) e recupera memórias formatadas para uso em prompts. Requer API key para autenticação e assinatura ativa. Requer configuração do Mem0.
- **Operation ID:** getMemories
- **Parameters:**
  - `message` (query): Opcional - Mensagem do usuário para adicionar à memória (opcional)
- **Responses:**
  - `200`: Memórias formatadas para prompts
  - `401`: 
  - `503`: Mem0 não configurado
  - `500`: 

## GET /tools/api/get-open-finance-connection-flow
- **Summary:** [PENDENTE]
- **Description:** Inicia o fluxo de conexão Open Finance via WhatsApp. Para usuários Premium, envia um fluxo interativo com lista de bancos. Para usuários Basic/Pro, envia notificação de acesso limitado. Requer API key para autenticação e assinatura ativa.
- **Operation ID:** getOpenFinanceConnectionFlow
- **Parameters:** Nenhum
- **Responses:**
  - `200`: Fluxo iniciado com sucesso
  - `400`: Dados do usuário incompletos
  - `401`: 
  - `500`: 

