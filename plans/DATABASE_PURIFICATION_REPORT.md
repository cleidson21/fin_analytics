# DATABASE PURIFICATION REPORT

Este documento consolida a visão final do schema de banco de dados (`database/schema_v2.sql`) gerado durante a FASE DB-01, realizando uma crítica de purificação em busca de legados ou redundâncias não aparentes, que preparam a fundação ótima para o Backend V3.

---

## 1. Inventário Geral
O `schema_v2.sql` atual é composto por **21 tabelas** ativas e mapeadas em Modelos e Repositórios. Na transição do banco V1 para o V2, diversas tabelas de relatórios estáticos (`relatorios`, `analises`) já foram devidamente extirpadas.

---

## 2. Ação por Tabela: KEEP, REVIEW, DELETE

### 🟢 KEEP (Manter 100%)
* `users`, `categories`, `goals`, `subscriptions` (Core Finance base).
* `import_runs`, `import_artifacts`, `audit_log` (Motor principal de Governança).
* `benchmarks`, `portfolio_evolution` (Motor analítico de Patrimônio).
* `rules`, `prompt_versions`, `ai_runs` (Inteligência modularizada).
* **Motivo:** Estruturas canônicas, totalmente testadas no BE-02 e sem sobreposições.

### 🟡 REVIEW (Revisar / Refatorar Colunas)
* `transactions` (Ledger do Core)
  * **Problema:** Possui as colunas FK `category_id` E colunas de texto `macro_categoria` / `sub_categoria` simultaneamente. As strings são flaggadas como legadas e fragmentam a tipagem hierárquica.
  * **Ação:** Em V3, abandonar `macro/sub_categoria` textual e depender 100% do relacionamento relacional com a tabela `categories`.
* `raw_events` (Data Lake)
  * **Problema:** Possui a coluna literal `metadata`. O nome da coluna cruza com palavras reservadas do SQLAlchemy, o que gerou mapeamento `metadata_json = Column("metadata", ...)` em `app/models/governance.py`.
  * **Ação:** O ideal é renomear no SQL para `metadata_json`.
* Tabelas de `staging_*` (`staging_imports`, `staging_positions`, `staging_dividends`, `staging_portfolio_evolution`)
  * **Problema:** Estão altamente tipadas (ID, Ticker, Values), mas como são tabelas temporárias voláteis, engessam a flexibilidade de parsers novos.
  * **Ação:** Considerar unificação para `JSONB` ou manter se a tipagem estrita ajudar na velocidade.

### 🔴 DELETE (Remover / Consolidar)
* `event_links`
  * **Problema:** Criada para Fuzzy Matching complexos (A liga com B). Contudo, a inteligência atual (`ReconciliationService`) atrela diretamente via hash cross_fingerprint no `raw_events` ou ignora os descartados. A complexidade de grafos dessa tabela nunca foi usada nos services escritos no BE-02.
  * **Ação:** Remover até que o requisito de "agrupamento n-para-m de lançamentos bancários" se faça real.

---

## 3. Conclusões de Campos (Nunca usados vs Faltantes)
* **Nunca Usados:** Tabela `rules` possui `miss_count`, `hit_count`, `evidence_count` e `superseded_by` que não foram implementados pelo `RuleEngineService` (que apenas lê a regex e responde).
* **Faltantes:** Não há tabelas explícitas de Extrato (Fatura) do Cartão de Crédito separadas do fluxo de CC (Checking Account), impedindo rateio de parcelamento complexo (o que obriga a coluna `parcelamento` em `transactions` a carregar strings simples tipo "1/10").
