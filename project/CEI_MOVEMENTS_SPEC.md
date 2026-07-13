# CEI Movements Specification (Homologação e Levantamento)

Este documento atesta a análise e especificação estrutural para o arquivo de **Movimentações/Negociação** gerado pela Área do Investidor da B3. Esta especificação é o contrato inviolável que guiará a implementação das camadas do domínio CEI (Reader, Parser e Normalizer).

## 1. Leitura e Registro (Homologação Física)

- **Arquivo:** `samples/Exemplo_Negociacao_B3.xlsx`
- **SHA256:** `a7847fb4c35e63a83258b1f874a520c6e5b37b65fd3d9663a76c034ccdeb566d`
- **Data da Leitura:** 2026-07-04/05
- **Tamanho Físico:** 5.365 bytes
- **Engine Utilizada:** `openpyxl`
- **Quantidade de Abas:** 1 (`Negociação`)
- **Quantidade de Linhas (aba Negociação):** 14
- **Quantidade de Colunas:** 10 (após extração do datetime original)
- **Cabeçalhos Encontrados:** `Data do Negócio`, `Tipo de Movimentação`, `Mercado`, `Prazo/Vencimento`, `Instituição`, `Código de Negociação`, `Quantidade`, `Preço`, `Valor`.
- **Valores Nulos e Duplicidades:** Zero (0).
- **Inventário:** 13 Compras, 1 Venda, 11 Ativos Distintos, 2 Instituições, 155 Dias de cobertura (30/12/2025 a 03/06/2026).
- **Campos Opcionais:** Prazo/Vencimento (pode conter hífens no mercado a vista).
- **Observações:** Warning `Workbook contains no default style`. Tickers com sufixo `F` (ex: `BBAS3F`).
*Origem: samples/Exemplo_Negociacao_B3.xlsx | Aba: Negociação | Leitura via pd.read_excel*

---

## 2. Estratégia de Integração e Independência de Domínios

O projeto conta com dois fluxos distintos que **não** devem se misturar:

*   **Arquivo de Custódia (`Exemplo_Ativos_B3.xlsx`)** → Domínio *Custódia*. Gera estritamente `PositionSnapshot` (o estado patrimonial de um instante).
*   **Arquivo de Negociação (`Exemplo_Negociacao_B3.xlsx`)** → Domínio *CEI*. Gera estritamente `Trade` ou `CorporateAction` (o fluxo financeiro / delta).

**Estratégia Oficial:** Os dois pipelines são e permanecerão independentes. Nenhum Reader de Custódia poderá ler abas de Negociação e vice-versa. Eles representam realidades diferentes (Estado vs. Evento).

---

## 3. Compatibilidade entre Arquivos e Auditoria de Sobreposição Temporal

*   **Custódia (`Exemplo_Ativos_B3.xlsx`):** Traz o estado congelado da carteira no momento da emissão.
*   **Negociação (`Exemplo_Negociacao_B3.xlsx`):** Traz o trajeto que levou ao estado. Abrange trades no período final de 2025 até junho de 2026.
*   **Sobreposição e Complementaridade:** **Não há sobreposição funcional**. O arquivo de negociação é complementar ao de custódia. O saldo final das negociações do arquivo `Exemplo_Negociacao` deve, teoricamente, empatar matematicamente com as cotas descritas no `Exemplo_Ativos`.
*   **Conflitos de Escrita:** Um arquivo **não** sobrescreve o outro no banco de dados, pois atuam em tabelas distintas (`position_snapshots` vs `trades`). Ambos coexistirão pacificamente.

---

## 4. Idempotência e Chave Natural

O arquivo da B3 **não exporta UUID** nem Número da Ordem em seu layout base. Sendo possível executar duas compras iguais do mesmo ativo, na mesma corretora e no mesmo preço no mesmo dia, a chave natural pura é arriscada.

**A Chave Natural Adotada será o hash composto:**
`MD5(Data do Negócio + Instituição + Código de Negociação + Tipo de Movimentação + Quantidade + Preço)`

**Estratégia Defensiva & Futura (B3):** Embora raras, duplicidades reais de negociação colidirão nesta matriz (ex: fracionar uma ordem na bolsa resulta em duas entradas iguais de mesmo preço no extrato). 
A estratégia de consolidação E2E determina que o Parser fará o GroupBy na chave e somará a quantidade financeira dos trades daquele dia se eles empatarem nesse MD5, gerando uma persistência resiliente. Se a B3 futuramente fornecer um `ID de Negócio` UUID, a arquitetura do MD5 será imediatamente aposentada e trocada pelo ID nativo.

---

## 5. Compatibilidade Futura

*   **Ordem das Colunas:** A ordem pode variar em exportações futuras. O `B3MovementsReader` deve ler os dados pelos **nomes dos cabeçalhos**, não pelos índices.
*   **Colunas Opcionais / Desconhecidas:** Qualquer coluna não listada nesta especificação deve ser solenemente ignorada (dropada) pelo Parser.
*   **Evolução Futura:** Se a B3 adicionar novas colunas de Taxas no futuro, o Parser Específico deverá ser versionado ou parametrizado, preservando a interface do `RawB3Movement`.
