# QUALITY METRICS E SLAS DE IMPORTAÇÃO

Este documento estabelece as métricas objetivas de qualidade (Service Level Agreements) que devem ser rigorosamente validadas durante o desenvolvimento vertical de cada fonte de dados na Fase 5.

## Métricas por Módulo

### 1. Reader
- **SLA:** 100% das linhas lidas corretamente a partir do arquivo bruto.
- **Evidência:** Contagem de itens no array de retorno (`RawDocument.rows`) batendo exatamente com a contagem de transações/linhas do arquivo original (ignorando cabeçalhos explícitos).

### 2. OCR (Para PDFs/Imagens)
- **SLA:** Taxa mínima de reconhecimento ≥ 99% para PDFs textuais nativos, ou tolerância aceitável via LLM em PDFs vetorizados.
- **Evidência:** Falhas de conversão de caracteres (ex: `$` lido como `S`) bloqueiam a inserção na Normalization caso afetem o cálculo financeiro.

### 3. Normalizer
- **SLA:** 100% dos registros do `RawDocument` convertidos com sucesso para a tipagem rigorosa do `CanonicalFinancialEvent` sem exceptions silenciosas.
- **Evidência:** O array final pós-normalização tem o mesmo tamanho do array válido lido pelo Reader.

### 4. Reconciliação (Reconciliation Engine)
- **SLA:** Zero duplicidades indevidas (Duplicate Key Exceptions ou Double Spending na interface).
- **Evidência:** Conflitos corretamente classificados (Igual, Complementar, Conflito Gravíssimo) utilizando a `23_SOURCE_PRIORITY_MATRIX.md`. Um envio duplo do mesmo arquivo resulta em 0 registros criados no segundo ImportRun.

### 5. Governança
- **SLA:** Rollback Validado em 100% dos casos de erro.
- **Evidência:** Se a importação abortar no meio, nenhum dado (incluindo lixo parcial) persiste na Base V3.

### 6. IA e Aprendizado
- **SLA:** Rastreabilidade obrigatória das classificações.
- **Evidência:** O sistema registrará na base se a categoria foi definida por "Regra/Regex", por "LLM Zero-Shot", ou por "Aprendizado Anterior (FAISS/Embeddings)".
