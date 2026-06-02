from decimal import Decimal
from datetime import date, datetime
from math import ceil
from pathlib import Path
import sqlite3

import pandas as pd


def _cents_to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return (Decimal(int(value)) / Decimal("100")).quantize(Decimal("0.01"))


class FinancialQueries:
    def __init__(self, db_path: Path = Path("fin_analytics.db")):
        self.db_path = db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _read_dataframe(self, query: str, numeric_columns: list[str]) -> pd.DataFrame:
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)

        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column])

        return df

    def _month_bounds(self, month: str) -> tuple[str, str]:
        month_start = datetime.strptime(month, "%Y-%m").date().replace(day=1)
        if month_start.month == 12:
            next_month = date(month_start.year + 1, 1, 1)
        else:
            next_month = date(month_start.year, month_start.month + 1, 1)

        return month_start.isoformat(), next_month.isoformat()

    def _build_transaction_filters(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        account: str | None = None,
        category: str | None = None,
        natureza: str | None = None,
    ) -> tuple[str, list[object]]:
        where_clauses: list[str] = []
        params: list[object] = []

        if start_date:
            where_clauses.append("data >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("data <= ?")
            params.append(end_date)

        if account:
            where_clauses.append("source = ?")
            params.append(account)

        if category:
            where_clauses.append("macro_categoria = ?")
            params.append(category)

        if natureza:
            where_clauses.append("natureza = ?")
            params.append(natureza)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return where_sql, params

    def get_cashflow_summary(self, month: str | None = None) -> pd.DataFrame:
        """Retorna Receitas e Gastos. Se 'month' for passado (ex: '2026-04'), filtra por esse mês."""
        query = """
            SELECT natureza, SUM(valor_cents) as total_cents
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

        if "total_cents" in df.columns:
            df["total"] = df["total_cents"].apply(_cents_to_decimal)
            df.drop(columns=["total_cents"], inplace=True)

        return df

    def get_expenses_by_category(self, month: str | None = None) -> pd.DataFrame:
        """Agrupa os gastos por Macro Categoria para o gráfico de barras/pizza."""
        query = """
            SELECT macro_categoria, ABS(SUM(valor_cents)) as total_cents
            FROM transactions
            WHERE natureza = 'EXPENSE' AND perfil != 'IGNORADO'
        """
        params: list[str] = []
        if month:
            query += " AND strftime('%Y-%m', data) = ?"
            params.append(month)

        query += " GROUP BY macro_categoria ORDER BY total_cents DESC"
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)

        if "total_cents" in df.columns:
            df["total"] = df["total_cents"].apply(_cents_to_decimal)
            df.drop(columns=["total_cents"], inplace=True)

        return df

    def get_daily_expenses(self, month: str | None = None) -> pd.DataFrame:
        """Retorna o total de gastos por dia para montar o heatmap mensal."""
        query = """
            SELECT data, ABS(SUM(valor_cents)) as total_cents
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

        if "total_cents" in df.columns:
            df["total"] = df["total_cents"].apply(_cents_to_decimal)
            df.drop(columns=["total_cents"], inplace=True)

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
            SELECT strftime('%Y-%m', data_pagamento) as month, SUM(valor_liquido_cents) as amount_received_cents
            FROM dividends
            GROUP BY month
            ORDER BY month ASC
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)

        if "amount_received_cents" in df.columns:
            df["amount_received"] = df["amount_received_cents"].apply(_cents_to_decimal)
            df.drop(columns=["amount_received_cents"], inplace=True)

        return df

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
                SUM(valor_cents) as total_cents
            FROM transactions
            WHERE natureza IN ('INCOME', 'EXPENSE')
            GROUP BY mes, natureza
            ORDER BY mes, natureza
        """
        df = self._read_dataframe(query, ["total_cents"])
        if "total_cents" in df.columns:
            df["total"] = df["total_cents"].apply(_cents_to_decimal)
            df.drop(columns=["total_cents"], inplace=True)
        return df

    def get_quarantine_transactions(self) -> pd.DataFrame:
        """Puxa o lixo/ruído que precisa de novas regras no rules.csv."""
        query = """
            SELECT data, descricao_original, valor_cents as valor_cents, identificador_externo
            FROM transactions
            WHERE macro_categoria = 'OUTROS'
               OR sub_categoria = 'INDEFINIDO'
            ORDER BY data DESC
        """
        df = self._read_dataframe(query, ["valor_cents"])
        if "valor_cents" in df.columns:
            df["valor"] = df["valor_cents"].apply(_cents_to_decimal)
            df.drop(columns=["valor_cents"], inplace=True)
        return df

    def get_import_status(self) -> dict[str, object]:
        query_last = """
            SELECT source_line_no, descricao_original
            FROM transactions
            WHERE origin = 'PIERRE'
              AND source_line_no IS NOT NULL
            ORDER BY source_line_no DESC
            LIMIT 3
        """
        query_next = """
            SELECT COALESCE(MAX(source_line_no), 0) + 1 AS next_line
            FROM transactions
            WHERE origin = 'PIERRE'
              AND source_line_no IS NOT NULL
        """

        with self._get_connection() as conn:
            last_df = pd.read_sql(query_last, conn)
            next_df = pd.read_sql(query_next, conn)

        last_items = [
            {
                "source_line_no": int(row["source_line_no"]),
                "description": row["descricao_original"],
            }
            for _, row in last_df.iterrows()
        ]

        next_line = int(next_df.iloc[0]["next_line"]) if not next_df.empty else 1
        return {"last_items": last_items, "next_line": next_line}

    def get_transactions(
        self,
        limit: int = 50,
        offset: int = 0,
        start_date: str | None = None,
        end_date: str | None = None,
        account: str | None = None,
        category: str | None = None,
        natureza: str | None = None,
    ) -> tuple[pd.DataFrame, int]:
        where_sql, params = self._build_transaction_filters(
            start_date=start_date,
            end_date=end_date,
            account=account,
            category=category,
            natureza=natureza,
        )

        count_query = f"SELECT COUNT(*) as total FROM transactions {where_sql}"
        items_query = f"""
            SELECT
                id_economico as id,
                data,
                descricao_original as description,
                macro_categoria as category,
                natureza,
                subnatureza,
                source as account,
                valor_cents as amount_cents
            FROM transactions
            {where_sql}
            ORDER BY data DESC, id_economico DESC
            LIMIT ? OFFSET ?
        """

        with self._get_connection() as conn:
            total_df = pd.read_sql(count_query, conn, params=params)

            items_params = [*params, limit, offset]
            items_df = pd.read_sql(items_query, conn, params=items_params)

        if "amount_cents" in items_df.columns:
            items_df["amount"] = items_df["amount_cents"].apply(_cents_to_decimal)
            items_df.drop(columns=["amount_cents"], inplace=True)

        total = int(total_df.iloc[0]["total"]) if not total_df.empty else 0
        return items_df, total

    def get_transactions_summary(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        account: str | None = None,
        category: str | None = None,
        natureza: str | None = None,
    ) -> dict[str, float]:
        where_sql, params = self._build_transaction_filters(
            start_date=start_date,
            end_date=end_date,
            account=account,
            category=category,
            natureza=natureza,
        )

        query = f"""
            SELECT
                COALESCE(SUM(CASE WHEN natureza = 'INCOME' THEN ABS(valor_cents) ELSE 0 END), 0) as income_cents,
                COALESCE(SUM(CASE WHEN natureza = 'EXPENSE' THEN ABS(valor_cents) ELSE 0 END), 0) as expense_cents,
                COALESCE(SUM(CASE WHEN natureza = 'INCOME' THEN ABS(valor_cents) ELSE 0 END), 0)
                - COALESCE(SUM(CASE WHEN natureza = 'EXPENSE' THEN ABS(valor_cents) ELSE 0 END), 0) as balance_cents
            FROM transactions
            {where_sql}
        """

        with self._get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)

        if df.empty:
            return {"income": Decimal("0.00"), "expense": Decimal("0.00"), "balance": Decimal("0.00")}

        row = df.iloc[0]
        return {
            "income": _cents_to_decimal(row["income_cents"] or 0),
            "expense": _cents_to_decimal(row["expense_cents"] or 0),
            "balance": _cents_to_decimal(row["balance_cents"] or 0),
        }

    def get_transactions_total_pages(self, total: int, limit: int) -> int:
        return ceil(total / limit) if total else 0

    def update_transaction_category(
        self,
        transaction_id: str,
        macro_categoria: str,
        natureza: str | None = None,
        subnatureza: str | None = None,
    ) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            current = cursor.execute(
                """
                SELECT macro_categoria, sub_categoria, subnatureza, natureza, perfil,
                       source_line_no, origin
                FROM transactions
                WHERE id_economico = ?
                """,
                (transaction_id,),
            ).fetchone()

            if current is None:
                return False

            natureza_final = natureza or current["natureza"]
            subnatureza_final = subnatureza or current["subnatureza"] or current["sub_categoria"]
            perfil_final = current["perfil"]

            cursor.execute(
                """
                UPDATE transactions
                SET macro_categoria = ?,
                    sub_categoria = ?,
                    subnatureza = ?,
                    natureza = ?,
                    classificacao_fonte = 'MANUAL',
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id_economico = ?
                """,
                (macro_categoria, subnatureza_final, subnatureza_final, natureza_final, transaction_id),
            )


            conn.commit()
            return cursor.rowcount > 0


    def get_accounts_summary(self) -> pd.DataFrame:
        query = "SELECT source as institution, SUM(valor_cents) as balance_cents FROM transactions GROUP BY source ORDER BY balance_cents DESC"
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)

        if "balance_cents" in df.columns:
            df["balance"] = df["balance_cents"].apply(_cents_to_decimal)
            df.drop(columns=["balance_cents"], inplace=True)

        return df

    def get_account_catalog(self) -> pd.DataFrame:
        query = "SELECT DISTINCT source as account FROM transactions ORDER BY account ASC"
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