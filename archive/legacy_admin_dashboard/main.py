import streamlit as st


st.set_page_config(
    page_title="FinAnalytics V2",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 FinAnalytics V2 - Operational Cockpit")
st.markdown("Este é o seu ambiente de validação de dados. O motor financeiro está a rodar perfeitamente.")
st.markdown("👈 **Navegue pelo menu lateral para auditar as suas métricas.**")

st.sidebar.success("Selecione um módulo acima.")