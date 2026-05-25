# FinAnalytics

FinAnalytics é uma plataforma local de inteligência financeira para consolidar, classificar e analisar transações pessoais com ETL incremental, DuckDB, Polars e um dashboard interativo em Streamlit.

## O que a plataforma faz

- Lê extratos CSV de diferentes fontes financeiras.
- Padroniza colunas e formatos de data, valor e texto.
- Classifica transações em receitas, gastos, investimentos e transferências.
- Gera um identificador determinístico para evitar duplicidades.
- Grava os dados curados em DuckDB e em Parquet particionado.
- Separa linhas inválidas ou não classificadas em quarentena.
- Exibe indicadores, gráficos e tabela de transações no dashboard.

## Estrutura principal

- `data/raw/`: coloque aqui os CSVs de origem.
- `data/processed/`: arquivos curados gerados pelo ETL.
- `data/database/`: banco local DuckDB.
- `logs/`: logs da execução.
- `app/dashboard.py`: interface web do Streamlit.
- `etl/pipeline.py`: execução completa do ETL.

## Passo a passo rápido

1. Ative o ambiente virtual do projeto.
2. Instale as bibliotecas da interface:

```powershell
pip install streamlit plotly
```

3. Coloque os arquivos CSV na pasta `data/raw/`.
4. Execute o ETL para carregar os dados novos:

```powershell
python etl/pipeline.py
```

5. Inicie o dashboard:

```powershell
streamlit run app/dashboard.py
```

6. Abra `http://localhost:8501` no navegador.

## Como inserir dados

O fluxo oficial de inserção é por CSV. Basta exportar ou salvar as transações em um arquivo compatível e colocá-lo em `data/raw/`.

Fontes reconhecidas pelo pipeline:

- `nubank`
- `myprofit`
- `manual`
- `sistema`

Se o caminho do arquivo contiver `myprofit`, `manual` ou `sistema`, o pipeline usa essa origem. Caso contrário, ele assume `NUBANK`.

Colunas mínimas esperadas no CSV bruto:

- `data`
- `descricao`
- `valor`

O sistema também aceita variações comuns como `date`, `desc`, `amount`, `tipo` e `categoria`.

## Como atualizar os dados

Sempre que um novo extrato chegar:

1. Salve o CSV em `data/raw/`.
2. Rode `python etl/pipeline.py` novamente.
3. O pipeline localiza apenas arquivos CSV.
4. Arquivos já processados com sucesso são ignorados automaticamente.
5. Somente registros novos entram em `BASE_GERAL`.
6. Linhas inválidas, incompletas ou não classificadas vão para `QUARANTINE_TRANSACTIONS`.

Isso permite reprocessar a pasta inteira sem duplicar dados.

Se você alterar as regras de categorização e quiser recalcular tudo de novo, use:

```powershell
python etl/pipeline.py --rebuild
```

Esse modo limpa a base local e reaplica as regras atuais sobre tudo que estiver em `data/raw/`.

O pipeline também aceita planilhas `.xlsx` de MyProfit, desde que elas estejam em `data/raw/` e tenham colunas equivalentes a `data`, `descricao` e `valor`.

## Funcionalidades do dashboard

### Barra lateral

- Seleção de período por data inicial e final.
- Painel de saúde do sistema com:
	- total de execuções do ETL,
	- itens em quarentena,
	- arquivos processados,
	- último status de execução.

### Indicadores principais

- Receita mensal.
- Gasto mensal.
- Total investido.
- Taxa de poupança.

### Abas disponíveis

- **Visão Geral**: linha temporal do fluxo líquido diário.
- **Distribuição de Gastos**: gastos por categoria com gráfico e tabela.
- **Investimentos**: aportes, dividendos e total investido.
- **Transações Recentes**: últimas movimentações curadas em tabela interativa.

## Regras de processamento

- Datas são aceitas em formatos comuns como `YYYY-MM-DD`, `DD/MM/YYYY` e `DD-MM-YYYY`.
- Valores monetários são normalizados para o padrão decimal interno.
- Transações de receita ficam positivas.
- Transações de gasto ficam negativas.
- O pipeline usa hash determinístico para reduzir duplicidades.
- O dashboard usa cache de 5 minutos para reduzir consultas repetidas.

## Troubleshooting

- Se o ETL informar que o banco está em uso, feche o Streamlit ou outro processo que esteja conectado ao DuckDB e tente novamente.
- Se um CSV falhar na leitura, verifique se ele contém `data`, `descricao` e `valor`.
- Se não aparecerem dados no dashboard, confirme se o ETL foi executado depois de inserir novos arquivos.

## Execução direta

Para validar rapidamente a camada analítica sem abrir o dashboard, use:

```powershell
python app/cli_test.py
```

Isso imprime um resumo formatado de cashflow, gastos por categoria, poupança e investimentos.
