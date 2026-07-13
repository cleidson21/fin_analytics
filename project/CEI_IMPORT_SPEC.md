# Especificação de Importação CEI (Área do Investidor - Movimentações)

Este documento define a arquitetura, estrutura esperada e estratégia de ingestão para os eventos transacionais históricos da B3 (antigo CEI - Canal Eletrônico do Investidor).

## 1. Levantamento Físico (`samples/`)

**Status:** Nenhum arquivo nativo de movimentação (CEI) foi localizado no diretório `samples/`. O arquivo `Exemplo_Ativos_B3.csv` contém apenas posições de custódia e proventos.
A arquitetura abaixo foi desenhada com base na padronização oficial da B3 para extratos de negociação (Área do Investidor).

### Estrutura Esperada
- **Formato Físico:** `.xlsx` (frequentemente com a extensão trocada para `.csv` pela B3).
- **Codificação:** UTF-8.
- **Engine Necessária:** `openpyxl`.
- **Planilha Alvo:** Tipicamente nomeada como `Movimentação` ou `Negociação`.
- **Delimitadores:** Formato estruturado em grade do Excel, sem delimitadores textuais.

### Cabeçalhos Padrão Esperados
1. `Data do Negócio` (Data da operação `DD/MM/YYYY`)
2. `Tipo de Movimentação` (Compra, Venda, Desdobramento, etc.)
3. `Mercado` (A Vista, Fracionário, Opções)
4. `Prazo/Vencimento`
5. `Instituição` (Corretora)
6. `Código de Negociação` (Ticker, ex: PETR4)
7. `Quantidade`
8. `Preço`
9. `Valor` (Quantidade * Preço)

---

## 2. Catálogo de Eventos Esperados

A camada de normalização CEI deve interpretar os seguintes "Tipos de Movimentação" para gerar objetos do tipo `CanonicalFinancialEvent` ou `Trade`:

* **Eventos Financeiros Básicos:**
  * `Compra` (Inflow de ativos, Outflow de caixa)
  * `Venda` (Outflow de ativos, Inflow de caixa)
  * `Transferência` (Mudança de custodiante, zero impacto em PNL)
* **Eventos Corporativos (Corporate Actions):**
  * `Bonificação em Ativos`
  * `Desdobramento` (Split)
  * `Grupamento` (Reverse Split)
  * `Subscrição` / `Exercício de Direitos`
  * `Amortização`
* **Ajustes:**
  * `Atualização`
  * `Fração em Dinheiro` (Liquidação de frações de desdobramento)

---

## 3. Arquitetura do Domínio (`backend/domains/investments/cei/`)

A Plataforma CEI adotará o mesmo padrão de orquestração puramente funcional utilizado na Custódia B3.

**Estrutura de Diretórios:**
```text
backend/domains/investments/cei/
├── readers/          # Leitura do XLSX e conversão em DataFrame
├── parsers/          # DataFrame para DTOs brutos (RawCEIEvent)
├── normalizers/      # RawCEIEvent para CanonicalFinancialEvent / Trade
├── pipelines/        # Orquestrador E2E funcional
├── dto.py            # Modelos de dados em Pydantic
├── repository/       # Persistência de Trades/Eventos via SQLAlchemy
├── services/         # Lógica de conciliação e hash
└── validators/       # Filtros de sanidade
```

---

## 4. Compatibilidade e Limites (Snapshot vs. Evento)

A distinção arquitetural entre a Macrofase 1 (Custódia) e a CEI é absoluta:

* **Snapshot (Custódia B3 / MyProfit):** Representa o **estado estático** (`PositionSnapshot`). Fotografia do patrimônio em uma data específica. Não conta a história, apenas o resultado.
* **Evento (CEI):** Representa o **delta transacional** (`Trade`, `CorporateAction`). Explica o trajeto do dinheiro e do ativo.

O pipeline do CEI não gerará `PositionSnapshot`. Ele converterá os dados em operações (`CanonicalFinancialEvent` ou entidade nativa `Trade`) que, futuramente, alimentarão as tabelas `trades` e `corporate_actions` da Sprint 2.

---

## 5. Matriz de Riscos

1. **Inconsistência de Ticker vs. ISIN:** A B3 frequentemente altera o sufixo do ticker no mercado fracionário (ex: `PETR4F` vs `PETR4`). O *Normalizer* deverá sanitizar isso cortando o `F` final.
2. **Eventos Duplicados ou Cancelados:** Diferente da custódia, transações históricas exigem uma chave de idempotência rigorosa baseada em `MD5(Data + Ticker + Instituição + Quantidade + Preço + Tipo)` para não duplicar compras em múltiplas execuções.
3. **Ausência de Taxas (Emolumentos / Corretagem):** O arquivo CEI não contém as taxas exatas da B3, apenas o preço de face da execução. O sistema deverá prever que o preço médio obtido do CEI é "Bruto" e diferirá da Nota de Corretagem oficial (que detém taxas).
4. **Múltiplos Layouts:** O formato do arquivo pode sofrer variações ao longo dos anos exportados.

---

## 6. Dependências para a Sprint 3B

Para iniciar a implementação (Sprint 3B), é **mandatório**:
- Um arquivo de amostra válido (CEI ou Movimentações B3) em `samples/`.
- Aprovação explícita desta arquitetura de separação CEI.
