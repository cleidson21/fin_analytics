# Relatório de Dependências Externas (External Dependency Report)

Este documento mapeia o acoplamento do sistema atual com as ferramentas Pierre e MyProfit, detalhando a estratégia técnica para eliminar definitivamente essas dependências.

---

## 1. Dependência: PIERRE

**Qual é a função atual do Pierre?**
O Pierre atua como um agregador e classificador. Ele consome o extrato sujo do Nubank e gera um extrato limpo ("normalizado"), categorizando gastos (ex: Lj Cacau Show -> Supermercado) e traduzindo o log do banco em algo digerível, utilizando LLM no processo.

**Por que é uma má dependência?**
Depender de normalização externa significa não ter controle sobre as regras de negócio e histórico de aprendizado da própria base de despesas. Além disso, o Pierre perde o rastreamento das faturas de cartão de crédito.

**Como eliminar (Arquitetura de Classificação Interna):**

A classificação será feita em casa através de um pipeline em 4 camadas de fallback ("Fall-Through Classification Pipeline"):

1. **Camada 1: Regras Determinísticas (Regex)**
   * **Ideal para**: PIX repetitivos, Pagamentos institucionais, RDB, Faturas.
   * *Exemplo*: `Regex("Transferência enviada pelo Pix - (.*)")` -> Extrai Contraparte, mapeia para `Transferências`. `Regex("Aplicação - Tesouro Selic")` -> Categoria `Investimentos`.
   * **Cobre**: ~60% das transações rotineiras.
2. **Camada 2: Merchant Mapping (Exato / Regras Manuais)**
   * **Ideal para**: Nomes de maquininhas e serviços conhecidos.
   * *Exemplo*: "EBW*Spotify" mapeia para Merchant "Spotify", Categoria "Streaming". "Lj Cacau Show 1/3" mapeia para "Cacau Show".
   * **Cobre**: ~20% adicionais.
3. **Camada 3: Embeddings & Vector Search (Opcional, mas Avançado)**
   * **Ideal para**: Transações nunca antes vistas, mas semanticamente similares a transações passadas.
   * *Implementação*: Transformar a descrição da transação em um vetor (via modelo local como `all-MiniLM-L6-v2` ou OpenAI) e buscar K-Nearest Neighbors no banco de `merchants` já mapeados.
   * **Cobre**: ~15% dos casos ambíguos.
4. **Camada 4: LLM Zero-Shot / Few-Shot (Fallback)**
   * **Ideal para**: Nomes completamente obscuros (ex: "075pestiscariaepizzari").
   * *Implementação*: Uma chamada barata a uma API de LLM (GPT-4o-mini ou Claude Haiku) pedindo para adivinhar a categoria com base na string bruta. Uma vez categorizado pelo LLM, o resultado é salvo na Camada 2 (Merchant Mapping) para que o sistema **nunca pergunte duas vezes** sobre o mesmo padrão.

**Conclusão Pierre**: O Pierre será substituído por um script cron que ingere CSV/OFX do Nubank e roda o pipeline acima.

---

## 2. Dependência: MYPROFIT

**Qual é a função atual do MyProfit?**
A ferramenta é usada como um "Livro Razão" (Ledger) de carteira. O usuário importa notas de corretagem lá, e a ferramenta cuida do trabalho sujo de matemática financeira: cálcular preço médio, dividendos, DY, YOC, rentabilidade TWR e cruzamento com benchmarks (IBOV, CDI).

**Por que é uma má dependência?**
O MyProfit funciona como uma "caixa preta". Os dados extraídos (Acoes.csv, Evolucao_carteira.csv) já estão processados, o que impede a auditoria fina dos trades, inviabiliza a criação de métricas customizadas exclusivas (ex: Alpha/Beta dinâmicos) e exige trabalho braçal de exportação/importação.

**Como eliminar (Motor Financeiro Interno):**

O sistema precisará assumir o cálculo matemático construindo as seguintes lógicas:

1. **Ingestão de Dados Primários (Single Source of Truth)**
   * *Como*: Ao invés de importar o extrato do MyProfit, o sistema V3 irá parsear diretamente o PDF das **Notas de Corretagem da B3** (utilizando bibliotecas como `pdfplumber` no Python ou serviços de extração estruturada). Alternativamente, consumirá dados do extrato da B3 (Área do Investidor).
   * *Objetivo*: Capturar cada compra/venda, taxas exatas, ISS, corretagem.

2. **Ingestão de Proventos**
   * *Como*: Lançamento automático com base em scraping do portal RI ou extratos da conta Nubank/NuInvest, e/ou importando relatórios do CEI (Canal Eletrônico do Investidor).

3. **Automação de Preço Médio (Cost Basis Engine)**
   * Construir uma função em Python/Pandas que, para cada ativo, iterativamente avalie o histórico de transações (`trades`) ordenadas cronologicamente.
   * Se compra: Aumenta quantidade, recalcula preço médio ponderado + custos.
   * Se venda: Deduz quantidade usando o preço médio atual para calcular Lucro/Prejuízo.
   * Se evento corporativo (Split 1:10): Multiplica quantidade por 10, divide preço médio por 10.

4. **Integração yfinance (Market Data)**
   * *Como*: Usar a biblioteca `yfinance` para baixar o fechamento diário (Close Price) de todos os `tickers` ativos na carteira.
   * Substitui completamente o dashboard do MyProfit ao multiplicar a Qtd Atual (calculada na etapa 3) pelo Preço Atual (`yfinance`).

5. **Motor de Benchmarks (Performance Engine)**
   * *Como*: Importar diariamente `^BVSP` (IBOV), `^SPX` (S&P 500) do yfinance. Para CDI e IPCA, integrar API gratuita do Banco Central do Brasil (SGS).
   * Com o valor da carteira diário (Snapshots) e cotas simuladas, aplicar a matemática descrita no catálogo de fórmulas para gerar a tabela de `Evolução Patrimonial` internamente.

**Conclusão MyProfit**: A importação atual de CSVs do MyProfit deve ser tratada estritamente como um "Migration Path" (apenas para carregar o histórico legado caso as Notas de Corretagem antigas tenham sido perdidas). No fluxo diário V3, o MyProfit deixará de existir no ecossistema.
