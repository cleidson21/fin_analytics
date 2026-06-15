# BE-02 SERVICE INVENTORY

**Mapeamento de Serviços Legados (V1) e Transição para Domínios V2**

## 1. Analytics & Financial (Core Finance Legacy)
* **Serviços V1:** `app/api/services/analytics.py`, `app/api/services/financial_service.py`, `app/api/routes/dashboard.py`.
* **Responsabilidade V1:** "God classes" responsáveis por somar receitas, despesas, calcular saldo e gerar gráficos JSON diretamente.
* **Complexidade:** Alta.
* **Para a V2:** Será quebrado em `CashflowService` (receitas/despesas/saldo), `InstallmentService` (lógica de parcelas solta no V1) e `GoalService`. O `SubscriptionService` será construído do zero (pois era texto livre no V1).
* **Prioridade de Reconstrução:** Altíssima (1).

## 2. Wealth & Market Data (Wealth Legacy)
* **Serviços V1:** `app/api/services/wealth.py`, `app/api/services/market_data.py`, `app/api/routes/investments.py`.
* **Responsabilidade V1:** Cálculo de posições, dividendos, fetch de CDI/IBOV na B3.
* **Complexidade:** Muito Alta (cálculo de preço médio e evolução).
* **Para a V2:** Transformado em `PositionService`, `DividendService`, `AllocationService` e `EvolutionService`.
* **Prioridade de Reconstrução:** Alta (2).

## 3. Governance & Import (Governance Legacy)
* **Serviços V1:** `app/api/services/governance_service.py`, `app/api/services/import_service.py`, `app/api/routes/governance.py`.
* **Responsabilidade V1:** Upload de arquivos, staging visualização e aprovação cruzada.
* **Complexidade:** Crítica (devido à Reconciliação).
* **Para a V2:** `ImportService`, `ReconciliationService` (Fuzzy Matching rígido), `ApprovalService` (promoção), `AuditService`.
* **Prioridade de Reconstrução:** Alta (2).

## 4. AI & Rules (AI Layer Legacy)
* **Serviços V1:** O antigo `categorizer.py` da raiz, `app/api/routes/learning.py`, `app/api/routes/prompts.py`.
* **Responsabilidade V1:** Inferencia OpenAI, Regex.
* **Complexidade:** Moderada a Alta.
* **Para a V2:** `RuleEngineService`, `PromptVersionService`, `ClassificationEngineService` (Fluxo obrigatório Reconciliation -> Rules -> AI -> Fallback) e `LearningService`.
* **Prioridade de Reconstrução:** Média (3) - Será feito após o motor básico Core/Governance.
