from decimal import Decimal

import streamlit as st

from database.queries import FinancialQueries
from utils.formatters import brl


st.set_page_config(page_title="Visão Geral", layout="wide")


@st.cache_data(show_spinner=False)
def carregar_dados():
    queries = FinancialQueries()
    return (
        queries.get_current_net_worth(),
        queries.get_cashflow_summary(),
        queries.get_expenses_by_category(),
        queries.get_dividend_history(),
        queries.get_monthly_cashflow(),
    )


st.header("📈 Visão Geral do Domínio")

net_worth, df_cash, df_expenses, df_divs, df_monthly = carregar_dados()

if df_cash.empty:
    st.warning("Nenhum dado encontrado. Execute o ETL primeiro (`python -m scripts.test_etl`).")
    st.stop()

receitas = df_cash.loc[df_cash["natureza"] == "INCOME", "total"].sum()
gastos = df_cash.loc[df_cash["natureza"] == "EXPENSE", "total"].sum()
saldo = receitas + gastos

if not isinstance(net_worth, Decimal):
    net_worth = Decimal(str(net_worth))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Patrimônio Total", brl(net_worth))
col2.metric("Receitas Operacionais", brl(receitas))
col3.metric("Gastos Operacionais", brl(gastos))
col4.metric("Saldo Líquido", brl(saldo))

st.divider()

colA, colB = st.columns(2)

with colA:
    st.subheader("Despesas por Macro Categoria")
    if not df_expenses.empty:
        df_expenses = df_expenses.set_index("macro_categoria")
        st.bar_chart(df_expenses["total"].abs())
    else:
        st.info("Sem dados de despesas.")

with colB:
    st.subheader("Evolução de Dividendos (Renda Passiva)")
    if not df_divs.empty:
        df_divs = df_divs.set_index("mes")
        st.bar_chart(df_divs["total_recebido"])
    else:
        st.info("Sem histórico de dividendos.")

st.divider()

st.subheader("Fluxo de Caixa Mensal")
if not df_monthly.empty:
    df_monthly = df_monthly.pivot(index="mes", columns="natureza", values="total").fillna(0)
    st.line_chart(df_monthly)
else:
    st.info("Sem dados de fluxo de caixa mensal.")