> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Matriz de Dependências — FIN Analytics

---

## Use Case × Repository Ports

| Use Case | Fase | Transaction | Account | Portfolio | Position | Dividend | Asset | Category | User | Institution | Provider |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AuthenticateUser | 1 | | | | | | | | ✅ | | |
| RefreshToken | 1 | | | | | | | | ✅ | | |
| GetAccounts (UC-11A) | 2 | | ✅ | | | | | | | ✅ | |
| GetCategoriesSummary (UC-11B) | 3 | ✅ | | | | | | ✅ | | | |
| GetTransactions | 3 | ✅ | | | | | | ✅ | | | |
| UpdateCategory | 3 | ✅ | | | | | | ✅ | | | |
| ConnectProvider | 5 | | | | | | | | | | ✅ |
| DisconnectProvider | 5 | ✅ | ✅ | | ✅ | ✅ | | | | | ✅ |
| SyncPierreAccounts | 5 | | ✅ | | | | | | | ✅ | ✅ |
| SyncPierreTransactions | 5 | ✅ | ✅ | | | | | ✅ | | | ✅ |
| GetPortfolio | 6 | | | ✅ | ✅ | ✅ | ✅ | | | | |
| GetDividends | 6 | | | ✅ | | ✅ | ✅ | | | | |
| SyncMyProfitPortfolio | 7 | | | ✅ | ✅ | ✅ | ✅ | | | | ✅ |
| SyncYFinanceQuotes | 7 | | | | ✅ | | ✅ | | | | |
| ImportCSV | 8 | ✅ | ✅ | | | ✅ | | ✅ | | | |
| ClassifyTransaction | 9 | ✅ | | | | | | ✅ | | | |
| GenerateInsights | 9 | ✅ | | | ✅ | ✅ | | | | | |
| GetDashboard | 10 | ✅ | ✅ | | ✅ | ✅ | | | | | |
| GetCashFlow | 10 | ✅ | ✅ | | | | | | | | |
| GetAlerts | 10 | ✅ | | | | | | | | | |
| BackupDatabase | 11 | — | — | — | — | — | — | — | — | — | — |

---

## Use Case × Provider Ports

| Use Case | Pierre | MyProfit | YFinance | Gemini | Notification |
|---|---|---|---|---|---|
| AuthenticateUser | | | | | |
| SyncPierreAccounts | ✅ | | | | |
| SyncPierreTransactions | ✅ | | | | |
| SyncMyProfitPortfolio | | ✅ | | | |
| SyncYFinanceQuotes | | | ✅ | | |
| ImportCSV | | | | | |
| ClassifyTransaction | | | | ✅ | |
| GenerateInsights | | | | ✅ | |
| GetDashboard | | | | | |
| GetTransactions | | | | | |

---

## Use Case × Eventos (Produz)

| Use Case | SyncStarted | SyncFinished | SyncFailed | TransactionImported | PortfolioUpdated | DividendReceived | CategoryClassified | InsightGenerated | ProviderDisconnected | BackupCreated |
|---|---|---|---|---|---|---|---|---|---|---|
| SyncPierreAccounts | ✅ | ✅ | ✅ | | | | | | | |
| SyncPierreTransactions | ✅ | ✅ | ✅ | ✅ | | | | | | |
| SyncMyProfitPortfolio | ✅ | ✅ | ✅ | | ✅ | ✅ | | | | |
| SyncYFinanceQuotes | | ✅ | ✅ | | ✅ | | | | | |
| ImportCSV | | | | ✅ | | ✅ | | | | |
| ClassifyTransaction | | | | | | | ✅ | | | |
| GenerateInsights | | | | | | | | ✅ | | |
| DisconnectProvider | | | | | | | | | ✅ | |
| BackupDatabase | | | | | | | | | | ✅ |

---

## Análise de Dependências Circulares

> [!NOTE]
> Verificação crítica: nenhum componente pode depender de camadas acima dele.

| Verificação | Status |
|---|---|
| Domain → Application | ❌ Não ocorre. Domínio não importa Application. |
| Domain → Infrastructure | ❌ Não ocorre. Domínio não conhece banco/HTTP. |
| Application → Domain | ✅ Correto — Application usa entidades do Domain. |
| Application → Ports | ✅ Correto — Application depende de Ports abstraídos. |
| Application → Infrastructure | ❌ Não deve ocorrer NUNCA — DIP (Application não conhece classes concretas). |
| Infrastructure → Application | ❌ Não ocorre. Infra implementa Ports, não usa UCs. |
| Provider → Domain | ❌ Não ocorre. Providers retornam `dict` bruto. |
| DTO → Provider | ❌ Não ocorre. DTOs são agnósticos. |
| Repository → REST | ❌ Não ocorre. Repositories acessam apenas banco. |
| **Dependências circulares** | **Nenhuma detectada** ✅ |

---

## Infraestrutura × Ports

| Implementação Concreta | Port |
|---|---|
| `SQLAlchemyTransactionRepository` | `ITransactionRepository` |
| `SQLAlchemyAccountRepository` | `IAccountRepository` |
| `SQLAlchemyPortfolioRepository` | `IPortfolioRepository` |
| `SQLAlchemyPositionRepository` | `IPositionRepository` |
| `SQLAlchemyDividendRepository` | `IDividendRepository` |
| `SQLAlchemyAssetRepository` | `IAssetRepository` |
| `SQLAlchemyCategoryRepository` | `ICategoryRepository` |
| `SQLAlchemyUserRepository` | `IUserRepository` |
| `SQLAlchemyProviderRepository` | `IProviderRepository` |
| `PierreRestAdapter` | `IPierreProvider` |
| `MyProfitSessionAdapter` | `IMyProfitProvider` |
| `YFinanceAdapter` | `IYFinanceProvider` |
| `GeminiAdapter` | `IGeminiProvider` |
| `RedisCache` / `InMemoryCache` | `ICache` |
| `StructuredLogger` | `ILogger` |
| `LocalFileStorage` | `IStorage` |
| `EnvSecretsAdapter` | `ISecrets` |
| `SystemClock` | `IClock` |
| `InProcessEventBus` | `IEventBus` |
