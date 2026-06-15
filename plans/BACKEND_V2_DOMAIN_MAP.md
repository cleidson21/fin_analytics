# BACKEND V2 DOMAIN MAP

**Alinhamento Tático de Domain-Driven Design (DDD)**

O Backend V2 rompe com a hierarquia horizontal MVC tradicional e implementa a estrutura por Bounded Contexts.

## 1. Core Finance
Lida com a tesouraria e o orçamento diário.
* **Entities:** `Transaction`, `Category`, `Goal`, `Subscription`.
* **Services/Repos:** Operam o fluxo de caixa (Cashflow) e o cálculo de metas/pacing. O `TransactionRepository` é o centro.

## 2. Wealth
Lida com a fotografia patrimonial.
* **Entities:** `Position`, `Dividend`, `PortfolioEvolution`, `Benchmark`.
* **Services/Repos:** Nunca alteram os dados contábeis diários, focando apenas no Delta Mensal (`Alpha`, `Rentabilidade`).

## 3. Governance
A porta de entrada e auditoria blindada.
* **Entities:** `ImportRun`, `ImportArtifact`, `StagingImport`, `StagingPosition`, `StagingDividend`, `StagingPortfolioEvolution`, `RawEvent`, `EventLink`, `AuditLog`.
* **Services/Repos:** Controlam as cascatas. Uma vez reprovado o `ImportRun`, nada atinge as camadas de Core/Wealth.

## 4. AI Layer
A Inteligência isolada.
* **Entities:** `Rule`, `PromptVersion`, `AiRun`.
* **Services/Repos:** Tratam de inferências locais (Memory JSON Rules) e inferências LLM (OpenAI) em background.
