# INVENTÁRIO DE TESTABILIDADE (FASE 9.5)

| Arquivo | Classe | Métodos Públicos | Dependências |
| ------- | ------ | ---------------- | ------------ |
| `app/api/services/auth_service.py` | `AuthService` | `authenticate_user`, `get_user`, `create_user` | `FinancialRepository`, `passlib` |
| `app/api/services/financial_service.py` | `FinancialService` | `get_transactions`, `get_transactions_summary`, `get_accounts_summary`, `get_cashflow_summary`, `get_current_net_worth` | `FinancialRepository` |
| `app/api/services/governance_service.py` | `GovernanceService` | `get_prompts`, `activate_prompt`, `get_learning_metrics`, `get_audit_logs`, `get_rules` | `GovernanceRepository` |
| `app/api/services/import_service.py` | `ImportService` | `process_import`, `rollback_import`, `promote_staging` | `GovernanceRepository`, `FinancialRepository` |

### Análise de Isolamento
- **Métodos puros**: Não encontrados nos Services (todos os métodos orquestram chamadas aos repositórios).
- **Métodos com acesso a Repository**: 100% dos métodos públicos das 4 classes de serviço acima acessam os Repositories.
- **Métodos que exigem Mock**: Todos. Nenhum teste unitário das regras de negócio dessas classes poderá ser executado sem injetar Mocks para as instâncias de `FinancialRepository` e `GovernanceRepository`.
