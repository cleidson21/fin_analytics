from database.queries import FinancialQueries


def testar_camada_analytics():
    queries = FinancialQueries()

    print("\n" + "=" * 60)
    print("TESTE DA CAMADA DE ANALYTICS (ETAPA 1.6)")
    print("=" * 60)

    df_cash = queries.get_cashflow_summary()
    print("\n[ FLUXO DE CAIXA OPERACIONAL ]")
    print(df_cash.to_string(index=False) if not df_cash.empty else "(sem dados)")

    df_monthly = queries.get_monthly_cashflow()
    print("\n[ FLUXO DE CAIXA MENSAL ]")
    print(df_monthly.to_string(index=False) if not df_monthly.empty else "(sem dados)")

    net_worth = queries.get_current_net_worth()
    print(f"\n[ PATRIMÔNIO ATUAL ]\nR$ {net_worth:,.2f}")

    df_divs = queries.get_dividend_history()
    print("\n[ HISTÓRICO DE DIVIDENDOS (Últimos 3 meses) ]")
    print(df_divs.tail(3).to_string(index=False) if not df_divs.empty else "(sem dados)")

    df_quarentena = queries.get_quarantine_transactions()
    print(f"\n[ QUARENTENA ]\n{len(df_quarentena)} transações pendentes de regra.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    testar_camada_analytics()