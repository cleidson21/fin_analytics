# DATABASE V2 MIGRATION ROADMAP

**Fase:** DB-01 (Database V2 Foundation)

## 1. ORDEM DE EXECUÇÃO DE CRIAÇÃO (Grafo de Dependência DDL)

Para que a *engine* SQL (SQLite ou SQLAlchemy) valide a criação do banco, a ordem estrita dos scripts é obrigatória:

**[Etapa 1] - Domínio Base (Sem Foreign Keys):**
* `users`, `categories` (Nova), `benchmarks` (Nova), `import_runs` (Obrigatório primeiro).

**[Etapa 2] - Entidades Filhas de Primeiro Grau:**
* `rules`, `prompt_versions`, `audit_log`, `subscriptions` (precisa de `categories`), `goals` (precisa de `categories`), `import_artifacts` (precisa de `import_runs`).

**[Etapa 3] - Buffer e IA (Segundo Grau):**
* `ai_runs` (precisa de `prompt_versions`), `raw_events` (precisa de `import_runs`), todas as tabelas `staging_*` (precisam de `import_runs`).

**[Etapa 4] - Ledger & Wealth (O Grau Final):**
* `transactions` (precisa de `import_runs` e `categories`), `positions` (precisa de `import_runs`), `dividends` (precisa de `import_runs`), `portfolio_evolution` (precisa de `import_runs`).
* `event_links` (precisa de `raw_events`).

## 2. PLANO DE MIGRAÇÃO DE DADOS (DML)
Após a subida estrutural limpa, o carregamento do patrimônio atual do usuário V1 para o V2 exigirá:

* **Sincronização de Inteligência:** Fazer o JOIN em memória da extinta `governance_rules` junto com a atual `rules` descartando duplicidades pela string de Regex (`pattern`).
* **MapReduce de Categorias:** Uma Query especial que roda num script extrairá todas as ocorrências de `transactions.macro_categoria` do banco antigo, e inserirá com ID UUID na nova tabela `categories`, guardando na memória o de-para (String -> UUID) para religar na nova `transactions`.

## 3. VALIDAÇÃO PÓS-MIGRAÇÃO
A certificação ocorrerá disparando 3 testes atômicos via script para testar as falhas estruturais (Constraints e Cascata). Caso qualquer erro diferente do programado ocorra, aplicaremos `Rollback`.
