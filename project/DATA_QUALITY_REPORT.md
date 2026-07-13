# Data Quality Report (Homologação Funcional CEI - Sprint 3C.1)

Este relatório atesta a auditoria física, temporal e de qualidade do arquivo de Movimentações (B3/CEI), cobrindo as Etapas 0 a 5 da homologação funcional.

## ETAPA 0 — LEITURA E REGISTRO DO PROJETO (RITUAL)
- **Documentações:** `01`, `02`, `04`, `06`, `09`, `10`, `B3_IMPORT_SPEC.md` e `CEI_MOVEMENTS_SPEC.md` foram lidas com sucesso. Constatou-se a ausência de `03_ARCHITECTURE.md`, `05_DATABASE_SPEC.md`, `07_CODING_STANDARD.md` e `08_DOMAIN_MAP.md` sob estas exatas nomenclaturas (existem equivalentes como `03_PHASE_STATUS.md`).
- **Estrutura de Diretórios:** Confirmada a existência de `backend/`, `database/`, `samples/`, `tests/`, `project/`, `frontend/`. O diretório raiz `imports/` não existe (possivelmente modulado sob o backend).
- **Consistência Documentação vs Código:** A auditoria atesta que *não há implementações órfãs relativas à Sprint 3C*. O domínio `cei/` ainda não existe no código, respeitando a fase puramente documental.
- **Novos Relatórios:** 4 matrizes adicionadas (este relatório, Pipeline Spec, Mapping Matrix, Compatibility Matrix).

## ETAPA 1 — LEITURA E REGISTRO DA AMOSTRA B3
- **Origem:** `samples/Exemplo_Negociacao_B3.xlsx`
- **SHA256:** `a7847fb4c35e63a83258b1f874a520c6e5b37b65fd3d9663a76c034ccdeb566d`
- **Tamanho:** 5.365 bytes
- **Engine Utilizada:** `openpyxl`
- **Data da Leitura:** 2026-07-04/05
- **Abas:** 1 (`Negociação`)
- **Dimensões:** 14 linhas x 9 colunas.
- **Cabeçalhos Exatos:** Data do Negócio, Tipo de Movimentação, Mercado, Prazo/Vencimento, Instituição, Código de Negociação, Quantidade, Preço, Valor.
- **Valores Nulos e Duplicidades:** Zero linhas nulas. Zero linhas estritamente duplicadas no Excel.
- **Células contendo "-":** `Prazo/Vencimento` contém hífens em 14/14 linhas. `Instituição` contém em 9/14 linhas (isso requer parser `replace('-', NaN)`).
- **Warnings Encontrados:** `Workbook contains no default style` gerado pela engine `openpyxl`.

## ETAPA 2 — INVENTÁRIO DOS DADOS
*Origem: samples/Exemplo_Negociacao_B3.xlsx | Aba: Negociação*
- **Operações (Total):** 14
- **Compras:** 13
- **Vendas:** 1
- **Ativos Distintos:** 11 (`BBAS3F`, `HGRU11`, `JSRE11`, `RBRY11`, `RZAK11`, `BBSE3F`, `GGBR4F`, `PRIO3F`, `TAEE11F`, `VALE3F`, `XPML11`)
- **Instituições Distintas:** 2
- **Mercados:** 2
- **Vencimentos:** 1
- **Datas Distintas:** 2

## ETAPA 3 — AUDITORIA TEMPORAL
- **Período Inicial (Primeiro Trade):** 30/12/2025
- **Período Final (Último Trade):** 03/06/2026
- **Dias Cobertos (Amplitude):** 155 dias
- **Datas sem Movimentação:** A esmagadora maioria dos dias, visto que só ocorreram trades em exatos 2 dias úteis dentro do delta de 155 dias.

## ETAPA 4 — AUDITORIA DE QUALIDADE (ANOMALIAS)
- **Tipos Inconsistentes / Tickers Inválidos:** Múltiplos tickers do mercado a vista/fracionário estão grafados com a letra `F` sufixal (ex: `BBAS3F`). *Isso causará fragmentação na carteira se não for sanitizado via Regex no Normalizer*.
- **Hifens em Texto:** O B3 insere hífens no lugar de brancos, afetando o parsing de colunas opcionais (Vencimento).
- **Linhas/Preços Inválidos:** Não detectados. Quantidades e preços são todos números float/int perfeitamente legíveis (positivos).

## ETAPA 5 — AUDITORIA DE SOBREPOSIÇÃO (Negociação vs Custódia)
Comparativo cruzado entre `Exemplo_Negociacao_B3.xlsx` e `Exemplo_Ativos_B3.xlsx`:
- **Ativos em Comum (10):** PRIO3, RZAK11, TAEE11, JSRE11, XPML11, BBSE3, HGRU11, VALE3, RBRY11, BBAS3. (Após normalizar o `F`).
- **Ativos Exclusivos de Negociação (1):** GGBR4 (indicando que foi comprado e vendido totalmente, zerando a posição no dia da custódia final, ou ainda não liquidado).
- **Ativos Exclusivos de Custódia (9):** KLBN4, MXRF11, KNCR11, Tesouro Selic 2029, HGRU12, BTHF11, Tesouro IPCA+ com Juros Semestrais 2035, Tesouro Selic 2031, TRXF11 (indicando que foram comprados antes de Dez/2025, período não coberto pelo arquivo atual).
- **Veredito:** Os arquivos são perfeitamente COMPLEMENTARES. Não existe sobreposição temporal-funcional. O primeiro relata a posição final, o segundo relata o fluxo para se chegar lá ou parte dele. Não há riscos de duplicação no banco de dados.
