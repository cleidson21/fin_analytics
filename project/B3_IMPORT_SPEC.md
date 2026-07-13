# B3 Import Specification (Levantamento Técnico)

Este documento atesta a análise estrutural dos arquivos exportados pela B3 (Área do Investidor) para balizar a construção do Reader e Parser da Sprint 1 (Custódia) e Sprint 2 (Proventos).

## 1. Visão Geral do Arquivo
- **Nome do Arquivo Físico:** `Exemplo_Ativos_B3.csv`
- **Extensão Real:** `.xlsx` (Zip Archive contendo XMLs de Excel). A B3 nomeia o arquivo incorretamente como `.csv`.
- **Formato Estrutural:** Workbook (Planilha) multi-abas.
- **Encoding:** `UTF-8` (implícito via parser XML do Excel).
- **Engine Necessária:** `openpyxl` associada ao `pandas` (`pd.read_excel(engine='openpyxl')`).

---

## 2. Estrutura de Planilhas (Sheets)
O arquivo é composto nativamente por 4 abas (sheets) contendo contextos patrimoniais e financeiros distintos:
1. `Posição - Ações`
2. `Posição - Fundos`
3. `Posição - Tesouro Direto`
4. `Proventos Recebidos`

---

## 3. Especificação por Planilha

### 3.1 Planilha: `Posição - Ações`
**Características:**
- Linhas de metadados antes do cabeçalho: Nenhuma (O cabeçalho encontra-se rigidamente na linha 0).
- Linhas de rodapé: Linhas finais contendo `Total` na coluna de Valor Atualizado, com as demais preenchidas com nulos.
- Células mescladas: Não detectadas no layout tabular.

**Cabeçalho e Colunas:**
- `Produto` (String) - Nome amigável.
- `Instituição` (String) - Nome da corretora custodiante.
- `Conta` (String/Int) - ID da conta na corretora.
- `Código de Negociação` **[Obrigatória]** (String) - Ticker da Ação.
- `CNPJ da Empresa` (String)
- `Código ISIN / Distribuição` (String)
- `Tipo` (String) - ON, PN, UNIT.
- `Escriturador` (String)
- `Quantidade` **[Obrigatória]** (Decimal)
- `Quantidade Disponível` (Decimal)
- `Quantidade Indisponível` (Decimal)
- `Motivo` (String)
- `Preço de Fechamento` (Decimal)
- `Valor Atualizado` (Decimal)

**Inconsistências & Estratégia de Leitura:**
1. A B3 usa strings como "-" para representar colunas nulas, o que quebra a tipagem decimal de imediato em algumas colunas (`Motivo`, `Quantidade Indisponível`). 
2. O parser precisará rodar `dropna(subset=['Código de Negociação'])` para filtrar as linhas de rodapé com totais nulos e agregados.

---

### 3.2 Planilha: `Posição - Fundos`
A estrutura é idêntica à de Ações, mas adaptada ao léxico de fundos.
**Cabeçalho Diferente:**
- A coluna `Código de Negociação` permanece existindo.
- A coluna `CNPJ da Empresa` se chama `CNPJ do Fundo`.
- A coluna `Escriturador` se chama `Administrador`.
- A coluna `Tipo` passa a reportar valores como "Cotas" ou "Direito" em vez de "ON/PN".

**Inconsistências & Estratégia de Leitura:**
- Ativos do tipo "Direito" (Subscrição) podem apresentar valores `0` e Preço `0`. Eles também poluem a visualização se não forem filtrados ou processados com cuidado.

---

### 3.3 Planilha: `Posição - Tesouro Direto`
A Renda Fixa possui colunas inteiramente distintas, pois o conceito muda de Ticker para ISIN.
**Cabeçalho Diferente:**
- `Produto` (Nome do Título, ex: 'Tesouro Selic 2029')
- `Instituição`
- `Código ISIN` **[Obrigatória]** (Chave de busca primária, pois Tesouro não tem Ticker simples).
- `Indexador` (IPCA, SELIC, PRE)
- `Vencimento` (Data `DD/MM/YYYY`)
- `Quantidade` **[Obrigatória]** (Pode conter casas decimais complexas, ex: 0.04)
- `Quantidade Disponível`
- `Quantidade Indisponível`
- `Motivo`
- `Valor Aplicado` (Principal de Custo)
- `Valor bruto`
- `Valor líquido`
- `Valor Atualizado`

**Inconsistências & Estratégia de Leitura:**
- Falta da coluna "Código de Negociação" (Ticker). O sistema precisará derivar ou aceitar o `Código ISIN` como fallback de Ticker ou normalizar nomes.
- As datas na coluna `Vencimento` vêm em formato brasileiro `DD/MM/YYYY` e exigirão coerção explícita.

---

### 3.4 Planilha: `Proventos Recebidos` (Apenas Referência para Sprint 2)
Não reflete custódia, e sim eventos de fluxo financeiro.
**Cabeçalho:**
- `Produto` (Ex: "TAEE11 - TRANSMISSORA ALIANCA...")
- `Pagamento` (Data em formato `DD/MM/YYYY`)
- `Tipo de Evento` (Dividendo, Rendimento)
- `Instituição` (Corretora recebedora)
- `Quantidade` (Decimal)
- `Preço unitário` (Decimal)
- `Valor líquido` (Decimal)

**Inconsistências & Estratégia de Leitura:**
- O arquivo concatena o Ticker e o Nome na mesma coluna (`Produto`), separados por " - ". O Ticker terá que ser extraído via Regex (`split(" - ")[0]`).

---

## 5. Requisitos para a Engine de Parsing
- Dependência absoluta à biblioteca `openpyxl`.
- Uma única execução do Reader precisará retornar múltiplos *batches*, um para cada *sheet* de interesse (Ações, Fundos, Tesouro).
- A engine deve aceitar tipos flutuantes e coercê-los ignorando hifens (`-`) inseridos na planilha como zeros/nulos.
