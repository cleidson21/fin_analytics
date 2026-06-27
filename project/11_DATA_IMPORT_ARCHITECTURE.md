# DATA IMPORT ARCHITECTURE & GOVERNANCE

Este documento define a arquitetura absoluta, matrizes de precedência e padrões de reconciliação para os motores de importação (Parsers) do FinAnalytics V3.

---

## 1. MATRIZ DE PRECEDÊNCIA (ATTRIBUTE-LEVEL CONFLICT RESOLUTION)

Quando duas fontes afirmarem valores distintos, a decisão será granular (por atributo) e não por documento inteiro.

| Atributo | Origem Oficial Vencedora | Confiabilidade | Justificativa |
|---|---|---|---|
| **Preço Médio** | Nota de Negociação | ★★★★★ | Reflete o custo exato, emolumentos e taxas B3 da operação. |
| **Quantidade de Ativos** | B3 | ★★★★★ | Custódia centralizada garante liquidação efetiva. |
| **Categoria** | Pierre | ★★★★☆ | Até a IA assumir totalmente, a heurística do agregador define a tag. |
| **Saldo Financeiro** | Conta Nubank | ★★★★★ | Lançamento efetivo e absoluto do débito/crédito na conta. |
| **Data de Pagamento** | Conta Nubank | ★★★★★ | D+2 (Notas) ou D+0 (Proventos) real liquidado pela câmara. |
| **Data COM** | MyProfit | ★★★★★ | Agregador fornece histórico de dividend yield de forma mais precisa que as faturas transacionais. |
| **Yield (DY/YOC)** | MyProfit | ★★★★☆ | Parâmetros de rentabilidade derivada (calculados). |
| **Corretagem/Taxas**| Nota de Negociação | ★★★★★ | Apenas a nota atesta emolumentos, ISS e taxa de liquidação B3. |

---

## 2. IDENTIDADE CANÔNICA DOS EVENTOS (ANTI-DUPLICAÇÃO)

A identidade única no banco (hash/UUID) previne repetições sucessivas da mesma carga.

* **PIX / Transferência / Pagamento na Conta:** Coluna `Identificador` nativo (UUID) do Nubank.
* **Compra Cartão de Crédito:** `hash(data_compra + valor + estabelecimento)`.
* **Nota de Corretagem Inteira:** `numero_nota + data_pregao + cnpj_corretora`.
* **Ordem de Ação (Linha da Nota):** `hash(numero_nota + ticker + quantidade + operacao)`.
* **Provento:** `hash(ticker + data_pagamento + valor_liquido)`.

---

## 3. MATRIZ DE RECONCILIAÇÃO (PAPEL DO DOCUMENTO)

* **Extrato Conta (Nubank):** Sempre **Cria** fluxo financeiro principal (`transactions`).
* **Fatura Cartão (Nubank):** Sempre **Cria** gastos vinculados a um faturamento de crédito.
* **Nota de Negociação:** Sempre **Cria** operações de trading e atualiza lote patrimonial.
* **B3 (Ativos):** Nunca cria fluxo de caixa. Apenas **Atualiza/Sobrescreve** a posição atual (`portfolio_position`).
* **MyProfit:** Nunca cria transação. Apenas **Enriquece** a posição com YOC, DY, Data COM.
* **Pierre:** Nunca cria transação. Apenas **Enriquece** a coluna `category_id` via correspondência de dados.

---

## 4. MATRIZ DE DUPLICIDADE (CRUZAMENTOS MÚLTIPLOS)

* **Cruzamento de Consumo Padrão:**
  `Compra Cartão (Gera)` -> `Fatura (Agrupa)` -> `Conta (Paga)` -> `Pierre (Categoriza)`
* **Cruzamento de Investimentos:**
  `Nota (Gera Compra)` -> `Conta (Gera Saída D+2)` -> `B3 (Atualiza Custódia)` -> `Pierre (Categoriza Saída D+2)`
* **Cruzamento de Proventos:**
  `MyProfit (Avisa)` -> `Conta (Recebe Fluxo)` -> `Pierre (Categoriza como Rendimento)`

---

## 5. MATRIZ DE IMPORTAÇÃO (ORDEM OBRIGATÓRIA)

A ordem de execução processual dos importadores (Parsers Pipeline) deve ser estrita:

1. **Conta Corrente (Nubank):** Gera a espinha dorsal de fluxo de caixa (via UUID forte). As demais tabelas âncoram nela.
2. **Fatura (Cartão):** Anexa os detalhamentos dos grandes saques ocorridos na Conta.
3. **Notas de Corretagem:** Define o fluxo oficial de Renda Variável.
4. **B3 (Custódia):** Concilia a somatória das Notas com a custódia efetiva real.
5. **MyProfit:** Injerta inteligência de dividendos na custódia B3.
6. **Pierre:** Roda no final, varrendo hashes já existentes no banco para carimbar o `category_id`.

---

## 6. MATRIZ DE CONFLITOS

| Conflito Identificado | Estratégia Adotada |
|---|---|
| Mesmo valor, Data diferente (ex: fim de semana) | Nubank (Conta) Vence. Tolerância de reconciliação D+2 útil. |
| Quantidade divergente (B3 x Notas inseridas) | B3 Vence (Reflete realidade). Alerta de `Missing Brokerage Note`. |
| Pagamento não identificado na conta (Provento) | Nubank Vence. Status `Pending Settlement` até cair no extrato real. |
| Saldo Financeiro impreciso (< R$ 1,00) | Gera transação silenciosa `Reconciliation Adjustment` (arredondamento). |
| Saldo Financeiro discrepante (> R$ 1,00) | Aborta parser. Engatilha **Rollback** instantâneo da ImportRun. |

---

## 7. MATRIZ DE APRENDIZADO DA IA (CLASSIFICAÇÃO)

O sistema substituirá gradualmente os agregadores externos (como Pierre) treinando modelos LLM/ML locais.

* **Features (Entradas):** `original_description` (do banco), `amount`, `day_of_month`.
* **Labels (Alvo):** `category_id`.
* **Professor (Teacher):** Os arquivos TXT do Pierre servirão como Ground Truth provisória.
* **Feedback Loop:** Toda vez que um usuário alterar uma categoria pré-sugerida pelo sistema, um evento `Feedback_Registered` é disparado, ajustando os pesos do Embedder.
* **Embeddings (Futuro):** O sistema vetorizará os nomes (ex: "Posto Shell" e "Posto Ale" terão similaridade cosseno alta, induzindo a IA a sugerir "Combustível" para ambos sem if/else duro).

---

## 8. MATRIZ DE GOVERNANÇA

* **ImportSession:** Sessão UI temporária contendo N arquivos para upload.
* **ImportBatch:** Ciclo de validação de tipagem e integridade do CSV/PDF.
* **ImportRun:** Gravação no Banco. Um `run_id` atômico abraça as mil linhas de um arquivo.
* **Rollback:** Exclusão em `CASCADE` usando a chave `run_id`. O banco V3 retorna imediatamente ao estado intocado caso a Matriz de Conflitos dispare "Erro Discrepante".
* **Audit Logs:** A tabela `import_audit` salvará as _metricas_ (500 criados, 3 alterados, 20 ignorados).
* **Reprocessamento:** O arquivo cru nunca é deletado do S3/disco antes da confirmação humana.

---

## 9. MATRIZ DE RASTREABILIDADE

Nenhum registro pode nascer no vácuo. Todo `transactions` ou `portfolio_position` deverá conter obrigatoriamente as colunas de lastro:

* `source_system`: VARCHAR (Ex: 'NUBANK_ACCOUNT', 'PIERRE', 'B3')
* `run_id`: UUID (FK apontando para a execução de importação específica)
* `external_uuid` / `external_hash`: VARCHAR (A chave canônica calculada na Etapa 2)
* `raw_data`: JSONB/JSON (O payload intacto da linha CSV extraída, útil para regressão)
