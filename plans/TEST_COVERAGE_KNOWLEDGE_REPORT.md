# TEST COVERAGE & KNOWLEDGE REPORT

Este documento cruza as regras de negócio e os cálculos financeiros vitais descobertos no Domínio V2 com a suíte de testes já construída na camada de Services, para assegurar que nada fundamental seja esquecido na refatoração ou construção da API.

---

## 1. Regras e Cálculos Cobertos (100% Validado)

O esforço massivo na fase *BE-02* providenciou forte cobertura testável isolada no SQLite em-memória (`check_same_thread=False`).

### Cobertos no Core Finance
* **Cálculo de Pacing (Ritmo de Gastos):** Coberto por `test_pacing_normal`, `test_pacing_mes_anterior_zero`. Garante que divisão por zero seja mitigada.
* **Consumo de Metas:** Validado o agrupamento da categoria e conversão dos `cents`.

### Cobertos no Wealth
* **Alpha vs Benchmark:** Coberto via mock dos índices IPCA e CDI no banco gerando deltas percentuais no `EvolutionService`.
* **Asset Allocation:** Validado matematicamente gerando 100% (pie chart) com agrupamento de `classe_ativo`.
* **YOC (Yield On Cost):** Validado em `test_dividends` agrupando lucros líquidos contra total investido no Snapshot mais recente.

### Cobertos na Governança
* **Fuzzy Matching (Reconciliação):** Amplamente coberto no `test_reconciliation.py`. Valida que se data diferir por mais de 3 dias, a reconciliação é barrada (Regra de Negócio Crucial).
* **Cascata ON DELETE:** Coberto no `test_approval.py` que apaga staging em rejeição de lote.

### Cobertos na AI Layer
* **Cascata de Prioridade (Regex Rule):** Coberto em `test_rule_engine_priority_conflict` no qual duas regras conflitantes são vencidas peloo `confidence_score` superior.
* **Pipeline Fallback AI:** Validado de ponta a ponta em `test_classification.py` garantindo que o Mock de AI classifique "UBER" como Transporte apenas se o RuleEngine falhar, e jogue para "Outros" em Fallback se ambos falharem.
* **Few-Shot Sampling:** Coberto em `test_learning.py` garantindo que transações com `classificacao_fonte='AI'` NÃO sejam listadas para treinar o Prompt.

---

## 2. Lacunas Mapeadas (Não Cobertos)

Apesar da lógica de Serviço estar imaculada, a auditoria revela "buracos estruturais" fora dos cálculos que precisam de testes durante a V3:

* **Injeção de Repositórios:** Como os Services estão chamando `db.query()` diretamente (falha de arquitetura relatada no GATE-01), os Repositórios recém-criados em `app/repositories/` **NÃO possuem cobertura**. Se houver um bug em `self.model(**obj_in)`, nós ainda não sabemos.
* **Resolução e Retorno DTO:** Nossos DTOs (`TransactionResponse`, `DashboardSummary`) não estão sendo testados na saída (serialização do SQLAlchemy para Pydantic).
* **API Endpoints (FastAPI):** Nenhuma rota (`app/api/routes`) foi testada em conjunto com os novos serviços V2 (visto que o V2 não escreveu APIs, apenas o "Core").

## 3. Conclusão da Cobertura
Nós possuímos **100% de cobertura no cérebro do sistema** (fórmulas, regras limitadoras, fluxos de conciliação). Contudo, possuímos **0% de cobertura nos "Portos e Adaptadores"** (Repositories e DTOs/Controllers HTTP). 

O foco da equipe em BE-03 não será validar matemática, será validar **Fluxo de Integração (Integration Tests)** entre Controller -> Service -> Repository.
