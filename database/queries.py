from decimal import Decimal
from datetime import date, datetime
from math import ceil
from pathlib import Path
import sqlite3

import pandas as pd


import math
def _cents_to_decimal(value) -> Decimal:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return Decimal("0.00")
    return (Decimal(int(value)) / Decimal("100")).quantize(Decimal("0.01"))


def classify_asset(ticker: str) -> str:
    t = ticker.upper()

    KNOWN_EXCEPTIONS = {
        "BOVA11": "ETFs (Brasil)",
        "SMAL11": "ETFs (Brasil)",
        "HASH11": "Criptomoedas",
        "IVVB11": "ETFs Globais",
        "KLBN11": "Ações Brasil",
        "TAEE11": "Ações Brasil",
        "TIET11": "Ações Brasil",
        "SANB11": "Ações Brasil",
    }

    if t in KNOWN_EXCEPTIONS:
        return KNOWN_EXCEPTIONS[t]

    if "RDB" in t or "TESOURO" in t or "CDB" in t:
        return "Renda Fixa"
    if t.endswith("11"):
        return "Fundos Imobiliários (FIIs)"
    if t.endswith("3") or t.endswith("4") or t.endswith("6"):
        return "Ações Brasil"
    if "BTC" in t or "ETH" in t:
        return "Criptomoedas"
    if t in ["IVV", "VXUS", "AGG"]:
        return "ETFs Globais"
    return "Outros"

def normalize_tipo_evento(tipo: str) -> str:
    if not tipo:
        return "OUTROS"
    
    t = tipo.upper().strip()
    if t in ["DIVIDENDO", "DIV", "DIVIDENDOS"]:
        return "DIVIDENDO"
    if t in ["JCP", "JUROS SOBRE CAPITAL PRÓPRIO", "JUROS SOBRE CAPITAL PROPRIO"]:
        return "JCP"
    if "RENDIMENTO" in t:
        return "RENDIMENTO"
    
    return "OUTROS"


from database.config import DATABASE_PATH

class FinancialQueries:
    def __init__(self, db_path: Path = DATABASE_PATH):
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
        """Agrupa os dividendos recebidos por Mês/Ano e os segrega por tipo de evento normalizado.
        Enriquece os dados com o histórico consolidado (proventos_cents) da tabela portfolio_evolution 
        caso os registros detalhados de dividendos estejam ausentes ou incompletos."""
        query_div = """
            SELECT strftime('%Y-%m', data_pagamento) as month, tipo_evento, valor_liquido_cents
            FROM dividends
        """
        query_evo = """
            SELECT strftime('%Y-%m', reference_month) as month, proventos_cents
            FROM portfolio_evolution
            WHERE proventos_cents > 0
        """
        with self._get_connection() as conn:
            df_div = pd.read_sql(query_div, conn)
            df_evo = pd.read_sql(query_evo, conn)

        pivot = pd.DataFrame(columns=["month", "DIVIDENDO", "JCP", "RENDIMENTO"])
        
        if not df_div.empty:
            df_div["tipo_norm"] = df_div["tipo_evento"].apply(normalize_tipo_evento)
            grouped = df_div.groupby(["month", "tipo_norm"])["valor_liquido_cents"].sum().reset_index()
            pivot = grouped.pivot(index="month", columns="tipo_norm", values="valor_liquido_cents").fillna(0).reset_index()
            
        for col in ["DIVIDENDO", "JCP", "RENDIMENTO"]:
            if col not in pivot.columns:
                pivot[col] = 0

        if not df_evo.empty:
            df_evo = df_evo.groupby("month")["proventos_cents"].sum().reset_index()
            if pivot.empty:
                pivot = df_evo.copy()
                pivot["DIVIDENDO"] = 0
                pivot["JCP"] = 0
                pivot["RENDIMENTO"] = 0
                pivot["OUTROS"] = 0
                pivot["proventos_cents_evo"] = pivot["proventos_cents"]
            else:
                pivot = pd.merge(pivot, df_evo, on="month", how="outer").fillna(0)
                pivot.rename(columns={"proventos_cents": "proventos_cents_evo"}, inplace=True)
        else:
            pivot["proventos_cents_evo"] = 0

        # Create final dataframe
        result = pd.DataFrame()
        result["month"] = pivot["month"]
        
        total_cents_div = pivot["DIVIDENDO"] + pivot["JCP"] + pivot["RENDIMENTO"]
        if "OUTROS" in pivot.columns:
            total_cents_div += pivot["OUTROS"]
            
        # Consider the max between detailed dividends and portfolio_evolution
        total_cents = pivot[["proventos_cents_evo"]].assign(div=total_cents_div).max(axis=1)
        diff = total_cents - total_cents_div
        
        # Add any difference (missing detail) to the generic 'DIVIDENDO' category so it shows in charts
        result["amount_dividend"] = (pivot["DIVIDENDO"] + diff).apply(_cents_to_decimal)
        result["amount_jcp"] = pivot["JCP"].apply(_cents_to_decimal)
        result["amount_rendimento"] = pivot["RENDIMENTO"].apply(_cents_to_decimal)
        
        if "OUTROS" in pivot.columns:
            result["amount_outros"] = pivot["OUTROS"].apply(_cents_to_decimal)
            
        result["amount_received"] = total_cents.apply(_cents_to_decimal)
        
        return result.sort_values(by="month").reset_index(drop=True)

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
            cursor = conn.cursor()
            last_rows = cursor.execute(query_last).fetchall()
            next_row = cursor.execute(query_next).fetchone()

        last_items = [
            {
                "source_line_no": int(row["source_line_no"]),
                "description": row["descricao_original"],
            }
            for row in last_rows
        ]

        next_line = int(next_row["next_line"]) if next_row and next_row["next_line"] is not None else 1
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
    ) -> tuple[list[dict], int]:
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
            cursor = conn.cursor()
            total = cursor.execute(count_query, params).fetchone()[0]

            items_params = [*params, limit, offset]
            rows = cursor.execute(items_query, items_params).fetchall()

        items = [
            {
                "id": row["id"],
                "data": row["data"],
                "description": row["description"],
                "category": row["category"],
                "natureza": row["natureza"],
                "subnatureza": row["subnatureza"],
                "account": row["account"],
                "amount": _cents_to_decimal(row["amount_cents"]),
            }
            for row in rows
        ]
        return items, total

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
            row = conn.cursor().execute(query, params).fetchone()

        if not row or row["income_cents"] is None:
            return {"income": Decimal("0.00"), "expense": Decimal("0.00"), "balance": Decimal("0.00")}

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


    def get_accounts_summary(self) -> list[dict]:
        query = "SELECT source as institution, SUM(valor_cents) as balance_cents FROM transactions GROUP BY source ORDER BY balance_cents DESC"
        with self._get_connection() as conn:
            rows = conn.cursor().execute(query).fetchall()

        return [
            {"institution": row["institution"], "balance": _cents_to_decimal(row["balance_cents"])}
            for row in rows
        ]

    def get_account_catalog(self) -> list[str]:
        query = "SELECT DISTINCT source as account FROM transactions ORDER BY account ASC"
        with self._get_connection() as conn:
            rows = conn.cursor().execute(query).fetchall()
        return [row["account"] for row in rows]

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

    def get_detailed_positions(self) -> pd.DataFrame:
        """Busca posições detalhadas do último snapshot disponível com cálculo de peso."""
        query = """
            SELECT
                ticker,
                quantidade,
                preco_medio,
                total_investido as valor_investido,
                preco_atual,
                total_atual as valor_atual,
                ganho
            FROM positions
            WHERE data_snapshot = (SELECT MAX(data_snapshot) FROM positions)
            ORDER BY total_atual DESC
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
            
        if df.empty:
            return df
            
        df["asset_class"] = df["ticker"].apply(classify_asset)
        df["asset_subclass"] = ""
            
        if "valor_atual" in df.columns:
            # Convert numeric columns explicitly
            df["valor_atual"] = pd.to_numeric(df["valor_atual"], errors='coerce').fillna(0)
            df["valor_investido"] = pd.to_numeric(df["valor_investido"], errors='coerce').fillna(0)
            df["ganho"] = pd.to_numeric(df["ganho"], errors='coerce').fillna(0)
            df["preco_medio"] = pd.to_numeric(df["preco_medio"], errors='coerce').fillna(0)
            df["preco_atual"] = pd.to_numeric(df["preco_atual"], errors='coerce').fillna(0)
            
            total_patrimonio = df["valor_atual"].sum()
            if total_patrimonio > 0:
                df["peso_percentual"] = (df["valor_atual"] / total_patrimonio) * 100
            else:
                df["peso_percentual"] = 0.0
        else:
            # Return empty DataFrame with expected columns if no data
            return pd.DataFrame(columns=[
                "ticker", "quantidade", "preco_medio", "valor_investido",
                "preco_atual", "valor_atual", "ganho", "peso_percentual"
            ])
            
        return df

    def get_dividends_by_asset(self) -> pd.DataFrame:
        """Busca o histórico completo de dividendos agrupado por ativo."""
        query = """
            SELECT 
                ticker,
                SUM(COALESCE(valor_liquido_cents, 0)) as total_recebido_cents,
                COUNT(*) as quantidade_eventos,
                MIN(data_pagamento) as primeiro_recebimento,
                MAX(data_pagamento) as ultimo_recebimento
            FROM dividends
            GROUP BY ticker
            ORDER BY total_recebido_cents DESC
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
            
        if "total_recebido_cents" in df.columns:
            df["total_recebido"] = df["total_recebido_cents"].apply(_cents_to_decimal)
            df.drop(columns=["total_recebido_cents"], inplace=True)
            
        return df


    def get_portfolio_evolution_history(self) -> pd.DataFrame:
        """Busca o histórico de evolução da carteira da nova tabela."""
        query = """
            SELECT
                strftime('%Y-%m', reference_month) as month,
                rentabilidade_mensal_pct,
                rentabilidade_acumulada_pct,
                patrimonio_cents,
                compras_cents,
                vendas_cents,
                op_finalizadas_cents,
                proventos_cents,
                ibov_mensal_pct,
                ibov_acumulado_pct,
                cdi_mensal_pct,
                cdi_acumulado_pct,
                ipca_mensal_pct,
                ipca_acumulado_pct,
                ifix_mensal_pct,
                ifix_acumulado_pct,
                sp500_mensal_pct,
                sp500_acumulado_pct,
                idiv_mensal_pct,
                idiv_acumulado_pct
            FROM portfolio_evolution
            ORDER BY reference_month ASC
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
            
        cents_cols = [
            "patrimonio_cents", "compras_cents", "vendas_cents", 
            "op_finalizadas_cents", "proventos_cents"
        ]
        
        for col in cents_cols:
            if col in df.columns:
                new_col = col.replace("_cents", "")
                df[new_col] = df[col].apply(_cents_to_decimal)
                df.drop(columns=[col], inplace=True)
                
        pct_cols = [
            "rentabilidade_mensal_pct", "rentabilidade_acumulada_pct",
            "ibov_mensal_pct", "ibov_acumulado_pct", "cdi_mensal_pct", 
            "cdi_acumulado_pct", "ipca_mensal_pct", "ipca_acumulado_pct", 
            "ifix_mensal_pct", "ifix_acumulado_pct", "sp500_mensal_pct", 
            "sp500_acumulado_pct", "idiv_mensal_pct", "idiv_acumulado_pct"
        ]
        for col in pct_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def get_portfolio_evolution_summary(self) -> dict:
        """Busca o resumo da evolução para KPIs."""
        query = """
            SELECT 
                (SELECT patrimonio_cents FROM portfolio_evolution ORDER BY reference_month DESC LIMIT 1) as patrimonio_atual_cents,
                (SELECT rentabilidade_acumulada_pct FROM portfolio_evolution ORDER BY reference_month DESC LIMIT 1) as rentabilidade_acumulada_pct,
                (SELECT ibov_acumulado_pct FROM portfolio_evolution ORDER BY reference_month DESC LIMIT 1) as ibov_acumulado_pct,
                (SELECT cdi_acumulado_pct FROM portfolio_evolution ORDER BY reference_month DESC LIMIT 1) as cdi_acumulado_pct,
                SUM(compras_cents) as compras_totais_cents,
                SUM(vendas_cents) as vendas_totais_cents,
                SUM(proventos_cents) as proventos_totais_cents
            FROM portfolio_evolution;
        """
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
            
        if df.empty or df.iloc[0]["patrimonio_atual_cents"] is None:
            return {
                "patrimonio_atual": Decimal("0.00"),
                "rentabilidade_acumulada": 0.0,
                "ibov_acumulado_pct": 0.0,
                "cdi_acumulado_pct": 0.0,
                "compras_totais": Decimal("0.00"),
                "vendas_totais": Decimal("0.00"),
                "proventos_totais": Decimal("0.00")
            }

        row = df.iloc[0]
        return {
            "patrimonio_atual": _cents_to_decimal(row["patrimonio_atual_cents"]),
            "rentabilidade_acumulada": float(row["rentabilidade_acumulada_pct"] or 0),
            "ibov_acumulado_pct": float(row["ibov_acumulado_pct"] or 0),
            "cdi_acumulado_pct": float(row["cdi_acumulado_pct"] or 0),
            "compras_totais": _cents_to_decimal(row["compras_totais_cents"]),
            "vendas_totais": _cents_to_decimal(row["vendas_totais_cents"]),
            "proventos_totais": _cents_to_decimal(row["proventos_totais_cents"])
        }

    def get_import_runs(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """Busca o histórico de importações recentes."""
        query = """
            SELECT 
                id, source_type, file_name, checksum, started_at, finished_at, 
                status, rows_read, rows_inserted, rows_updated, rows_failed, created_by
            FROM import_runs
            ORDER BY started_at DESC
            LIMIT ? OFFSET ?
        """
        with self._get_connection() as conn:
            rows = conn.cursor().execute(query, [limit, offset]).fetchall()
        return [dict(row) for row in rows]

    def get_dashboard_metrics(self) -> dict:
        """Busca KPIs globais para o Dashboard de Governança."""
        query = """
            SELECT
                COUNT(id) as total_runs,
                SUM(CASE WHEN status = 'CONFIRMED' THEN 1 ELSE 0 END) as confirmed_runs,
                SUM(CASE WHEN status IN ('PENDING', 'AWAITING_CONFIRMATION', 'PROCESSING', 'PROCESSING_CONFIRMATION') THEN 1 ELSE 0 END) as pending_runs,
                COALESCE(SUM(rows_inserted), 0) as lines_inserted,
                COALESCE(SUM(rows_updated), 0) as lines_updated,
                COALESCE(SUM(rows_failed), 0) as lines_failed,
                MAX(started_at) as last_import
            FROM import_runs
            WHERE source_type != 'LEGACY'
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query).fetchone()
            
            if not row:
                return {
                    "total_runs": 0, "confirmed_runs": 0, "pending_runs": 0,
                    "lines_inserted": 0, "lines_updated": 0, "lines_failed": 0,
                    "last_import": None
                }
                
            return {
                "total_runs": row["total_runs"] or 0,
                "confirmed_runs": row["confirmed_runs"] or 0,
                "pending_runs": row["pending_runs"] or 0,
                "lines_inserted": row["lines_inserted"] or 0,
                "lines_updated": row["lines_updated"] or 0,
                "lines_failed": row["lines_failed"] or 0,
                "last_import": row["last_import"]
            }

    def get_import_run_by_id(self, run_id: str) -> dict | None:
        """Busca os detalhes de uma importação específica, incluindo error_log e preview_summary."""
        query = """
            SELECT 
                id, source_type, file_name, checksum, started_at, finished_at, 
                status, rows_read, rows_inserted, rows_updated, rows_failed, created_by, error_log, preview_summary
            FROM import_runs
            WHERE id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (run_id,)).fetchone()
            return dict(row)

    def get_wealth_staging_items(self, run_id: str) -> dict:
        import json
        run = self.get_import_run_by_id(run_id)
        if not run:
            return {"file_type": "UNKNOWN", "items": []}
            
        file_type = "UNKNOWN"
        if run.get("preview_summary"):
            try:
                summary = json.loads(run["preview_summary"])
                file_type = summary.get("file_type", "UNKNOWN")
            except:
                pass
                
        items = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if file_type == "POSICOES":
                cursor.execute(
                    "SELECT source_line_no, ticker, validation_status, validation_message FROM staging_positions WHERE import_run_id = ? ORDER BY source_line_no ASC",
                    (run_id,)
                )
                items = [dict(r) for r in cursor.fetchall()]
            elif file_type == "PROVENTOS":
                cursor.execute(
                    "SELECT source_line_no, ticker, validation_status, validation_message FROM staging_dividends WHERE import_run_id = ? ORDER BY source_line_no ASC",
                    (run_id,)
                )
                items = [dict(r) for r in cursor.fetchall()]
            elif file_type == "EVOLUCAO":
                cursor.execute(
                    "SELECT source_line_no, reference_month as ticker, validation_status, validation_message FROM staging_portfolio_evolution WHERE import_run_id = ? ORDER BY source_line_no ASC",
                    (run_id,)
                )
                items = [dict(r) for r in cursor.fetchall()]
            elif run.get("source_type") == "PIERRE":
                cursor.execute(
                    "SELECT source_line_no, description as ticker, status as validation_status, NULL as validation_message FROM staging_imports WHERE import_run_id = ? ORDER BY source_line_no ASC",
                    (run_id,)
                )
                items = [dict(r) for r in cursor.fetchall()]
                
        return {"run_id": run_id, "file_type": file_type, "items": items}

    def get_asset_position(self, ticker: str) -> dict | None:
        """Busca o snapshot mais recente de um ativo específico."""
        query = """
            SELECT
                ticker,
                quantidade,
                preco_medio,
                total_investido as valor_investido,
                preco_atual,
                total_atual as valor_atual,
                ganho
            FROM positions
            WHERE ticker = ? AND data_snapshot = (SELECT MAX(data_snapshot) FROM positions WHERE ticker = ?)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (ticker, ticker)).fetchone()
            
            if not row:
                return None
                
            pos = {
                "ticker": row[0],
                "quantidade": row[1],
                "preco_medio": row[2],
                "valor_investido": row[3],
                "preco_atual": row[4],
                "valor_atual": row[5],
                "ganho": row[6] if row[6] != 0 else (row[5] - row[3])
            }
            pos["asset_class"] = classify_asset(pos["ticker"])
            pos["asset_subclass"] = ""
            return pos

    def get_asset_dividends(self, ticker: str) -> list:
        """Busca histórico completo de proventos de um ativo."""
        query = """
            SELECT data_pagamento, tipo_evento, valor_liquido
            FROM dividends
            WHERE ticker = ?
            ORDER BY data_pagamento DESC
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query, (ticker,)).fetchall()
            
            return [
                {
                    "data": r[0],
                    "tipo": r[1],
                    "valor": r[2]
                }
                for r in rows
            ]

    def get_asset_timeline(self, ticker: str) -> list:
        """
        Gera uma timeline de eventos historicamente comprováveis.
        Eventos:
        - Primeiro registro na base (primeiro provento)
        - Primeiro dividendo recebido
        - Maior dividendo recebido
        """
        events = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Proventos
            divs = cursor.execute("SELECT data_pagamento, valor_liquido FROM dividends WHERE ticker = ? ORDER BY data_pagamento ASC", (ticker,)).fetchall()
            
            if divs:
                first_div = divs[0]
                events.append({
                    "date": first_div[0],
                    "title": "Primeiro Provento Recebido",
                    "description": f"Recebimento inaugural de R$ {first_div[1]:.2f}",
                    "type": "MILESTONE"
                })
                
                max_div = max(divs, key=lambda x: x[1])
                # Evita duplicar se o maior também for o primeiro
                if max_div[0] != first_div[0] or len(divs) > 1:
                    events.append({
                        "date": max_div[0],
                        "title": "Maior Recebimento Histórico",
                        "description": f"Provento recorde de R$ {max_div[1]:.2f}",
                        "type": "RECORD"
                    })
                    
            # Outros marcos poderiam vir de import_runs ou snapshots antigos se tivéssemos.
            # Por hora limitamos ao comprovável em dividends, respeitando a regra estrita do usuário.

        events.sort(key=lambda x: x["date"], reverse=True)
        return events

    def get_asset_cashflow(self, ticker: str) -> list[dict]:
        """
        Busca o histórico de eventos financeiros (cashflow) de um ativo.
        Usa a tabela raw_events do ETL v2 para cruzar dividendos e compras/vendas.
        """
        query = """
            SELECT 
                event_date as date,
                amount_cents,
                event_type as type,
                source,
                metadata
            FROM raw_events
            WHERE json_extract(metadata, '$.ticker') = ?
               OR json_extract(metadata, '$.descricao_original') LIKE ?
            ORDER BY event_date DESC
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            rows = cursor.execute(query, (ticker, f"%{ticker}%")).fetchall()
            
            return [
                {
                    "date": r["date"],
                    "amount": _cents_to_decimal(r["amount_cents"]) if r["amount_cents"] is not None else 0,
                    "type": r["type"],
                    "source": r["source"],
                    "metadata": __import__("json").loads(r["metadata"] or "{}")
                }
                for r in rows
            ]

    def get_database_summary(self) -> dict:
        summary = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            summary['total_transactions'] = cursor.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            summary['total_positions'] = cursor.execute("SELECT COUNT(*) FROM positions").fetchone()[0]
            summary['total_dividends'] = cursor.execute("SELECT COUNT(*) FROM dividends").fetchone()[0]
            summary['total_evolutions'] = cursor.execute("SELECT COUNT(*) FROM portfolio_evolution").fetchone()[0]
            summary['total_import_runs'] = cursor.execute("SELECT COUNT(*) FROM import_runs").fetchone()[0]
            summary['runs_confirmed'] = cursor.execute("SELECT COUNT(*) FROM import_runs WHERE status = 'CONFIRMED'").fetchone()[0]
            summary['runs_pending'] = cursor.execute("SELECT COUNT(*) FROM import_runs WHERE status IN ('PENDING', 'AWAITING_CONFIRMATION')").fetchone()[0]
        return summary

    def get_database_tables(self) -> list:
        tables = ['transactions', 'positions', 'dividends', 'portfolio_evolution', 'import_runs', 'staging_imports', 'staging_positions', 'staging_dividends', 'staging_portfolio_evolution']
        results = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for t in tables:
                try:
                    count = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    results.append({'table_name': t, 'row_count': count, 'status': 'OK' if count < 1000000 else 'WARNING'})
                except:
                    results.append({'table_name': t, 'row_count': 0, 'status': 'ERROR'})
        return results

    def get_database_integrity(self) -> dict:
        integrity = {'orphan_runs': 0, 'pending_staging': 0, 'duplicate_transactions_suspects': 0}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Orphan runs (runs in transactions that don't exist in import_runs)
            integrity['orphan_runs'] = cursor.execute("SELECT COUNT(DISTINCT import_run_id) FROM transactions WHERE import_run_id IS NOT NULL AND import_run_id NOT IN (SELECT id FROM import_runs)").fetchone()[0]
            # Pending staging
            integrity['pending_staging'] = cursor.execute("SELECT COUNT(*) FROM staging_imports WHERE status = 'PENDING'").fetchone()[0]
            # Duplicate suspects (same value, date, description, macro)
            integrity['duplicate_transactions_suspects'] = cursor.execute("SELECT COUNT(*) FROM (SELECT data, descricao_original, valor_cents, COUNT(*) as c FROM transactions GROUP BY data, descricao_original, valor_cents HAVING c > 1)").fetchone()[0]
        return integrity

    def get_audit_runs(self, status_filter: str = 'ALL') -> list:
        query = "SELECT id, file_name, source_type, started_at, status, created_by, rows_read, rows_inserted, rows_updated, rows_failed FROM import_runs"
        params = []
        if status_filter != 'ALL':
            if status_filter == 'CONFIRMED': query += " WHERE status = 'CONFIRMED'"
            elif status_filter == 'PENDING': query += " WHERE status IN ('PENDING', 'AWAITING_CONFIRMATION', 'PROCESSING_CONFIRMATION')"
            elif status_filter == 'ROLLBACK': query += " WHERE status = 'CANCELLED'"
            elif status_filter == 'ERROR': query += " WHERE status = 'FAILED'"
        query += " ORDER BY started_at DESC"
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            return [dict(row) for row in cursor.execute(query, params).fetchall()]

    def get_audit_rollbacks(self) -> list:
        query = "SELECT id, file_name, rollback_timestamp, rollback_user, rollback_reason, started_at FROM import_runs WHERE status = 'CANCELLED' ORDER BY rollback_timestamp DESC"
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            return [dict(row) for row in cursor.execute(query).fetchall()]

    def get_audit_logs(self, entity_type: str = None, action: str = None, changed_by: str = None, start_date: str = None, end_date: str = None, limit: int = 100, offset: int = 0) -> list:
        query = "SELECT id, entity_type, entity_id, action, field_changes, changed_by, created_at FROM audit_log WHERE 1=1"
        params = []
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        if action:
            query += " AND action = ?"
            params.append(action)
        if changed_by:
            query += " AND changed_by = ?"
            params.append(changed_by)
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            return [dict(row) for row in cursor.execute(query, params).fetchall()]

    def get_audit_log_by_id(self, log_id: str) -> dict:
        query = "SELECT id, entity_type, entity_id, action, field_changes, changed_by, created_at FROM audit_log WHERE id = ?"
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            row = cursor.execute(query, (log_id,)).fetchone()
            if row:
                return dict(row)
            return None

    def get_admin_positions(self, limit: int = 50, offset: int = 0, ticker: str = None, snapshot_date: str = None, classe_ativo: str = None) -> tuple[list, int]:
        where_clauses = ["1=1"]
        params = []
        if ticker:
            where_clauses.append("ticker LIKE ?")
            params.append(f"%{ticker}%")
        if snapshot_date:
            where_clauses.append("data_snapshot = ?")
            params.append(snapshot_date)
        if classe_ativo:
            where_clauses.append("classe_ativo = ?")
            params.append(classe_ativo)
            
        where_str = " AND ".join(where_clauses)
        
        count_query = f"SELECT COUNT(*) FROM positions WHERE {where_str}"
        query = f"SELECT ticker, data_snapshot, quantidade, preco_medio, total_atual as valor_total, classe_ativo, observacao FROM positions WHERE {where_str} ORDER BY data_snapshot DESC, ticker ASC LIMIT ? OFFSET ?"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            total = cursor.execute(count_query, params).fetchone()[0]
            
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            items = []
            for row in cursor.execute(query, params + [limit, offset]).fetchall():
                d = dict(row)
                d["snapshot_date"] = d.pop("data_snapshot")
                d["preco_medio"] = _cents_to_decimal(d.get("preco_medio"))
                d["valor_total"] = _cents_to_decimal(d.get("valor_total"))
                items.append(d)
                
            return items, total

    def get_admin_dividends(self, limit: int = 50, offset: int = 0, ticker: str = None, start_date: str = None, end_date: str = None, tipo_evento: str = None) -> tuple[list, int]:
        where_clauses = ["1=1"]
        params = []
        if ticker:
            where_clauses.append("ticker LIKE ?")
            params.append(f"%{ticker}%")
        if start_date:
            where_clauses.append("data_pagamento >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("data_pagamento <= ?")
            params.append(end_date)
        if tipo_evento:
            where_clauses.append("tipo_evento = ?")
            params.append(tipo_evento)
            
        where_str = " AND ".join(where_clauses)
        
        count_query = f"SELECT COUNT(*) FROM dividends WHERE {where_str}"
        query = f"SELECT id_economico, ticker, tipo_evento, valor_liquido_cents as valor, data_pagamento, observacao FROM dividends WHERE {where_str} ORDER BY data_pagamento DESC LIMIT ? OFFSET ?"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            total = cursor.execute(count_query, params).fetchone()[0]
            
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            items = []
            for row in cursor.execute(query, params + [limit, offset]).fetchall():
                d = dict(row)
                d["valor"] = _cents_to_decimal(d.get("valor"))
                items.append(d)
                
            return items, total

    def get_admin_categories(self, limit: int = 50, offset: int = 0) -> tuple[list, int]:
        count_query = "SELECT COUNT(DISTINCT macro_categoria) FROM transactions WHERE macro_categoria IS NOT NULL AND macro_categoria != ''"
        query = "SELECT macro_categoria as categoria, COUNT(*) as quantidade_transacoes FROM transactions WHERE macro_categoria IS NOT NULL AND macro_categoria != '' GROUP BY macro_categoria ORDER BY quantidade_transacoes DESC LIMIT ? OFFSET ?"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            total = cursor.execute(count_query).fetchone()[0]
            
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            items = [dict(row) for row in cursor.execute(query, [limit, offset]).fetchall()]
                
            return items, total

    def get_reconciliation_inbox(self) -> dict:
        import json
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            suggestions_query = """
                SELECT el.*, 
                       a.source as a_source, a.event_type as a_type, a.amount_cents as a_amount, a.event_date as a_date, a.metadata as a_meta,
                       b.source as b_source, b.event_type as b_type, b.amount_cents as b_amount, b.event_date as b_date, b.metadata as b_meta
                FROM event_links el
                LEFT JOIN raw_events a ON el.event_id_a = a.id
                LEFT JOIN raw_events b ON el.event_id_b = b.id
                WHERE el.status = 'SUGGESTED'
            """
            suggestions_raw = cursor.execute(suggestions_query).fetchall()
            
            suggestions = []
            for row in suggestions_raw:
                d = dict(row)
                d["event_a"] = {
                    "id": d["event_id_a"],
                    "source": d["a_source"],
                    "event_type": d["a_type"],
                    "event_date": d["a_date"],
                    "amount_cents": d["a_amount"],
                    "metadata": json.loads(d["a_meta"] or "{}") if d["a_meta"] else {}
                }
                d["event_b"] = {
                    "id": d["event_id_b"],
                    "source": d["b_source"],
                    "event_type": d["b_type"],
                    "event_date": d["b_date"],
                    "amount_cents": d["b_amount"],
                    "metadata": json.loads(d["b_meta"] or "{}") if d["b_meta"] else {}
                }
                for k in ["a_source", "a_type", "a_amount", "a_date", "a_meta", "b_source", "b_type", "b_amount", "b_date", "b_meta"]:
                    d.pop(k, None)
                suggestions.append(d)
                
            orphans_query = """
                SELECT id, source, event_type, amount_cents, event_date, metadata
                FROM raw_events
                WHERE pipeline_status = 'PROMOTED'
                  AND id NOT IN (SELECT event_id_a FROM event_links)
                  AND id NOT IN (SELECT event_id_b FROM event_links)
                ORDER BY event_date DESC
                LIMIT 100
            """
            orphans_raw = cursor.execute(orphans_query).fetchall()
            orphans = []
            for r in orphans_raw:
                od = dict(r)
                od["metadata"] = json.loads(od["metadata"] or "{}") if od["metadata"] else {}
                orphans.append(od)
            
            return {
                "suggestions": suggestions,
                "orphans": orphans
            }
