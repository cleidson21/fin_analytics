import streamlit as st

from database.queries import FinancialQueries


st.set_page_config(page_title="Quarentena", layout="wide")


@st.cache_data(show_spinner=False)
def carregar_quarentena():
    queries = FinancialQueries()
    return queries.get_quarantine_transactions()


st.header("🏥 Quarentena (Auditoria Semântica)")
st.markdown("Lista de transações que o motor classificou como `OUTROS / INDEFINIDO`.")

df_quarentena = carregar_quarentena()

if df_quarentena.empty:
    st.success("🎉 Motor 100% ajustado! Nenhuma transação pendente.")
else:
    st.warning(f"{len(df_quarentena)} transações requerem regras no `taxonomy/rules.csv`.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.dataframe(df_quarentena, width="stretch", hide_index=True)

    with col2:
        st.write("🔥 **Padrões de Ruído (Top Frequência)**")
        freq = df_quarentena["descricao_original"].value_counts().reset_index()
        freq.columns = ["Descrição Original", "Ocorrências"]
        st.dataframe(freq, width="stretch", hide_index=True)