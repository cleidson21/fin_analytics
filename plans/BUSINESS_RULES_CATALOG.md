# BUSINESS RULES CATALOG

Este catálogo documenta formalmente todas as regras de negócios intrínsecas ao FinAnalytics V2, extraídas do código, relatórios e suítes de testes.

---

## 1. Regras Críticas (Impeditivas)

### R-01: Exclusão em Cascata do Lifecycle (Import Runs)
* **Classificação:** CRÍTICA
* **Descrição:** Se uma Importação (`import_run_id`) for deletada ou sofrer Rollback por motivo de falha de conciliação ou recusa humana, TODAS as entidades (Ledger, Staging, RawEvents, Audit, Evoluções, AI Runs) atreladas àquele lote devem ser excluídas automaticamente via banco.
* **Fórmula/Mecanismo:** `ON DELETE CASCADE` imposto diretamente no Schema SQL (`schema_v2.sql`) ao invés do nível de aplicação.
* **Dependências:** ORM Constraint / Database FK.
* **Origem:** `Governance Domain` / `schema_v2.sql`.

### R-02: Pipeline Híbrido de Classificação Inteligente
* **Classificação:** CRÍTICA
* **Descrição:** Nenhuma transação pode contornar a fila de classificação em 4 etapas (Reconciliation -> Rules -> AI -> Fallback).
* **Fórmula/Mecanismo:** 
  1. Já Reconciliada? Ignora.
  2. Bate com Regra Forte? Associa e para.
  3. LLM/AI classifica.
  4. Cai em `Outros`.
* **Dependências:** `RuleEngineService`, `ClassificationEngineService`.
* **Origem:** `AI Layer Domain` / `test_classification.py`.

### R-03: Conciliação Temporal e Financeira (Fuzzy Matching)
* **Classificação:** CRÍTICA
* **Descrição:** Dois eventos brutos (ou Staging vs Ledger) só podem ser linkados sozinhos se a janela de dias entre a data de compensação na instituição e no OFX for inferior ao *Threshold*.
* **Fórmula/Mecanismo:** Diferença em Dias (`abs(DataA - DataB) <= 3 dias`) E Valores Exatos em Centavos (Centavos A == Centavos B).
* **Dependências:** Conversão estrita em `_cents` (impede floats quebrados do Python).
* **Origem:** `ReconciliationService` / `V2_GOVERNANCE_AND_BOOTSTRAP.md`.

---

## 2. Regras Altas (Integridade)

### R-04: Prioridade de Conflito Semântico (Regex Rule)
* **Classificação:** ALTA
* **Descrição:** Se uma Transação Bate com duas regras de Regex (ex: "UBER" na regra 1 e "UBER EATS" na regra 2), a de maior peso prevalece.
* **Fórmula/Mecanismo:** `ORDER BY confidence_score DESC LIMIT 1`.
* **Dependências:** Engine deve varrer todas as ativas antes de abortar.
* **Origem:** `RuleEngineService` / `test_rule_engine.py`.

### R-05: Singleton de Active Prompt
* **Classificação:** ALTA
* **Descrição:** É terminantemente proibido o sistema possuir mais de 1 `PromptVersion` onde `active == 1`.
* **Fórmula/Mecanismo:** Na ativação de um prompt, emite-se um UPDATE massivo setando todos os ativos para `0`, comitado em uma única transaction isolada com a ativação.
* **Dependências:** `PromptVersionService`.
* **Origem:** `app/services/ai_layer/prompt_versions.py`.

---

## 3. Regras Médias (Processamento / Exibição)

### R-06: Purificação de Contexto de IA (Few-Shot)
* **Classificação:** MÉDIA
* **Descrição:** O motor de aprendizado contínuo (Few-Shot Prompting) só tem permissão de usar como métrica Transações onde a origem da classificação (`classificacao_fonte`) tenha sido intervenção direta humana, para não criar viés de confirmação (AI ensinando AI).
* **Fórmula/Mecanismo:** `WHERE classificacao_fonte IN ('USER', 'MANUAL')`.
* **Dependências:** `Transaction`, `LearningService`.
* **Origem:** `app/services/ai_layer/learning.py`.

---

## 4. Regras Baixas (UI/Notificações)

### R-07: Degradação de Metas
* **Classificação:** BAIXA
* **Descrição:** O sistema define que a flag de severidade (`severity_level`) para o Frontend exibe GOOD/WARNING/DANGER caso o limite da meta orçamentária chegue perto do teto de limite antes do tempo.
* **Fórmula/Mecanismo:** Se Consumo >= 80% (WARNING). Se >= 100% (DANGER).
* **Dependências:** Visualização Dashboards.
* **Origem:** Schema Core Finance (`goals`).
