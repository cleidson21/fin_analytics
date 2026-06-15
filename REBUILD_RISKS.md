# REBUILD RISKS ANALYSIS - FASE 10.2

Documento de rastreabilidade de passivos estruturais e riscos altos levantados no planejamento da reconstrução do Fin Analytics V2.

---

## 1. RISCOS DA RECONSTRUÇÃO
* **Perda da "Fotografia do Passado":** Ao recriar a arquitetura, pode haver corrupção do formato consolidado de histórico. O risco engloba a quebra de tipagem (`camelCase` vs `snake_case`) destruindo todos os Gráficos de Evolução Patrimonial (Recharts) que dependem visceralmente do DTO espelhado no Frontend.
* **Corrupção por Cascata Incompleta:** O sistema de governança é pautado no Lote de Importação (`import_runs`). Se o time subestimar a importância da Foreign Key com `ON DELETE CASCADE`, qualquer rejeição de importação futura vazará na tela como "Gasto Morto".

## 2. DEPENDÊNCIAS CRÍTICAS
* **ETL Pipeline & Governança:** Este é o coração do sistema. O banco de dados NÃO pode assumir dados injetados de fora do processo da Staging (Auditoria). Toda via deve passar por `Importação (Parser)` -> `Raw (Deduplicação Hash)` -> `Staging (Buffer)` -> `Aprovação Humana` -> `Ledger (Core)`.
* **API_CONTRACT_FREEZE.md:** O arquivo absoluto de limites (Boundary Contract). A branch de Frontend V2 depende 100% que as rotas mapeadas lá sejam mantidas sob as mesmas URIs sem modificação no comportamento.

## 3. COMPONENTES DE ALTO ACOPLAMENTO (Forte Fragilidade)
* **`WealthAnalyticsService` (Backend) & Banco de Dados Core:** Este serviço realiza cruzamentos orgânicos densos. Ele junta simultaneamente a tabela `positions`, o histórico `portfolio_evolution` e puxa lógicas de YOC sob a `dividends`. Refatorar as queries brutas deste serviço exige cautela máxima.
* **`EventReconciler` e `EventClassifier` (ETL IA):** Ambos agem entrelaçados. O Classifier acata a ordem imperativa de *Negative Match* e *Fuzzy Links* gerados no Reconciler. Alterar a matemática de qualquer um dos módulos destrói a Categorização visual de gastos, empurrando lançamentos bancários valiosos para o limbo do "Indefinido".

## 4. MÓDULOS QUE EXIGEM VALIDAÇÃO MATEMÁTICA ESTRITA
Qualquer squad assumindo a reengenharia deve cravar 100% de cobertura nos seguintes testes de função:
1. **Delta de Alpha:** Validar se a subtração aritmética do rendimento diário contra o IBOV/CDI permanece estática, conforme regras extraídas.
2. **Pacing de Gastos Mensais (`% Delta`):** A matemática de "Trending Up/Down" exige testes focados para cenários onde a despesa do Mês Anterior foi `0` (ZeroDivisionError protection).
3. **Bucket de Parcelamentos:** O agrupamento iterativo das parcelas usando a tolerância dividida (`round(amount/10)`) é vital para que compras do mesmo nome com variação de centavos no banco não explodam como "Novas Compras".
4. **Data de Contexto Estático:** Nenhum destes módulos pode avaliar `is_active` invocando relógio do servidor, mas sim atrelando-se eternamente a `max(data) importada` pela Governança.
