from decimal import Decimal
from pathlib import Path
import sqlite3

import pandas as pd


class FinancialQueries:
    def __init__(self, db_path: Path = Path("fin_analytics.db")):
        self.db_path = db_path

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _read_dataframe(self, query: str, numeric_columns: list[str]) -> pd.DataFrame:
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)

        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column])

        return df

    def get_cashflow_summary(self, month: str | None = None) -> pd.DataFrame:
        """Retorna Receitas e Gastos. Se 'month' for passado (ex: '2026-04'), filtra por esse mês."""
        query = """
            SELECT natureza, SUM(valor) as total
            FROM transactions
            WHERE natureza IN ('INCOME', 'EXPENSE')
        """
        params: list[str] = []
        if month:
            query += " AND strftime('%Y-%m', data) = ?"
            params.append(month)

        query += " GROUP BY natureza"

        with self._get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)

        if "total" in df.columns:
            df["total"] = pd.to_numeric(df["total"])

        return df

    def get_expenses_by_category(self, month: str | None = None) -> pd.DataFrame:
        """Agrupa os gastos por Macro Categoria para o gráfico de barras/pizza."""
        query = """
            SELECT macro_categoria, ABS(SUM(valor)) as total
            FROM transactions
            WHERE natureza = 'EXPENSE' AND perfil != 'IGNORADO'
        """
        params: list[str] = []
        if month:
            query += " AND strftime('%Y-%m', data) = ?"
            params.append(month)

        query += " GROUP BY macro_categoria ORDER BY total DESC"
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)

        if "total" in df.columns:
            df["total"] = pd.to_numeric(df["total"])

        return df

    def get_daily_expenses(self, month: str | None = None) -> pd.DataFrame:
        """Retorna o total de gastos por dia para montar o heatmap mensal."""
        query = """
            SELECT data, ABS(SUM(valor)) as total
            FROM transactions
            WHERE natureza = 'EXPENSE' AND perfil != 'IGNORADO'
        """
        params: list[str] = []
        if month:
            query += " AND strftime('%Y-%m', data) = ?"
            params.append(month)

        query += " GROUP BY data ORDER BY data"

        with self._get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)

        if "total" in df.columns:
            df["total"] = pd.to_numeric(df["total"])

        return df

    def get_current_net_worth(self) -> Decimal:
        """Calcula o Patrimônio Total atual com base no snapshot mais recente."""
        query = """
            SELECT SUM(total_atual) as net_worth
            FROM positions
            WHERE data_snapshot = (SELECT MAX(data_snapshot) FROM positions)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()[0]
            return Decimal(str(result)) if result is not None else Decimal("0")

    def get_dividend_history(self) -> pd.DataFrame:
        """Agrupa os dividendos recebidos por Mês/Ano com arredondamento direto no banco."""
        query = """
            SELECT strftime('%Y-%m', data_pagamento) as month, ROUND(SUM(valor_liquido), 2) as amount_received
            FROM dividends
            GROUP BY month
            ORDER BY month ASC
        """
        with self._get_connection() as conn:
            return pd.read_sql(query, conn)

    def get_portfolio_allocation(self) -> pd.DataFrame:
        """Agrupa o património atual por Asset Class com dicionário de exceções para ETFs/Units."""
        query = """
            SELECT ticker, total_atual
            FROM positions
            WHERE data_snapshot = (SELECT MAX(data_snapshot) FROM positions)
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            return df

        def classify_asset(ticker: str) -> str:
            t = ticker.upper()

            KNOWN_EXCEPTIONS = {
                "BOVA11": "ETFs (Brazil)",
                "SMAL11": "ETFs (Brazil)",
                "HASH11": "Cryptocurrency",
                "IVVB11": "Global ETFs",
                "KLBN11": "Brazilian Stocks",
                "TAEE11": "Brazilian Stocks",
                "TIET11": "Brazilian Stocks",
                "SANB11": "Brazilian Stocks",
            }

            if t in KNOWN_EXCEPTIONS:
                return KNOWN_EXCEPTIONS[t]

            if "RDB" in t or "TESOURO" in t or "CDB" in t:
                return "Fixed Income"
            if t.endswith("11"):
                return "Real Estate (FIIs)"
            if t.endswith("3") or t.endswith("4") or t.endswith("6"):
                return "Brazilian Stocks"
            if "BTC" in t or "ETH" in t:
                return "Cryptocurrency"
            if t in ["IVV", "VXUS", "AGG"]:
                return "Global ETFs"
            return "Others"

        df["asset_class"] = df["ticker"].apply(classify_asset)

        allocation = df.groupby("asset_class")["total_atual"].sum().reset_index()
        allocation.rename(columns={"total_atual": "current_total"}, inplace=True)
        allocation["current_total"] = pd.to_numeric(allocation["current_total"])
        return allocation.sort_values(by="current_total", ascending=False)

    def get_monthly_cashflow(self) -> pd.DataFrame:
        """Retorna o fluxo de caixa mensal por natureza."""
        query = """
            SELECT
                strftime('%Y-%m', data) as mes,
                natureza,
                SUM(valor) as total
            FROM transactions
            WHERE natureza IN ('INCOME', 'EXPENSE')
            GROUP BY mes, natureza
            ORDER BY mes, natureza
        """
        return self._read_dataframe(query, ["total"])

    def get_quarantine_transactions(self) -> pd.DataFrame:
        """Puxa o lixo/ruído que precisa de novas regras no rules.csv."""
        query = """
            SELECT data, descricao_original, valor, identificador_externo
            FROM transactions
            WHERE sub_categoria = 'INDEFINIDO'
            ORDER BY data DESC
        """
        return self._read_dataframe(query, ["valor"])

    def get_transactions(self, limit: int = 50, offset: int = 0) -> pd.DataFrame:
        query = "SELECT data, descricao_original as description, macro_categoria as category, source as account, valor as amount FROM transactions ORDER BY data DESC LIMIT ? OFFSET ?"
        with self._get_connection() as conn:
            return pd.read_sql(query, conn, params=[limit, offset])

    def get_accounts_summary(self) -> pd.DataFrame:
        query = "SELECT source as institution, SUM(valor) as balance FROM transactions GROUP BY source ORDER BY balance DESC"
        with self._get_connection() as conn:
            return pd.read_sql(query, conn)

    def get_net_worth_history(self) -> pd.DataFrame:
        """Busca o Património Total do ÚLTIMO dia registado de cada mês."""
        query = """
            SELECT
                strftime('%Y-%m', data_snapshot) as month,
                SUM(total_atual) as net_worth
            FROM positions
            WHERE data_snapshot IN (
                SELECT MAX(data_snapshot)
                FROM positions
                GROUP BY strftime('%Y-%m', data_snapshot)
            )
            GROUP BY month
            ORDER BY month ASC
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)

        if "net_worth" in df.columns:
            df["net_worth"] = pd.to_numeric(df["net_worth"])

        return df