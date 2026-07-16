import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AdvisorRepository:
    def get_latest_portfolio_snapshot(self, session: Session) -> Dict[str, Any]:
        query = text("""
            SELECT 
                total_equity, cost_basis, dividends_total, 
                cumulative_twr, sharpe_ratio, beta_ibov, volatility_annual
            FROM portfolio_snapshots
            ORDER BY date DESC
            LIMIT 1
        """)
        row = session.execute(query).fetchone()
        if not row:
            return {
                "patrimonio_atual": 0.0,
                "patrimonio_investido": 0.0,
                "patrimonio_liquido": 0.0,
                "dividendos_acumulados": 0.0,
                "rentabilidade_historica": 0.0,
                "sharpe": 0.0,
                "beta": 0.0,
                "volatilidade": 0.0
            }
        
        equity = float(row[0]) / 100.0 if row[0] else 0.0
        cost = float(row[1]) / 100.0 if row[1] else 0.0
        
        return {
            "patrimonio_atual": equity,
            "patrimonio_investido": cost,
            "patrimonio_liquido": equity - cost,
            "dividendos_acumulados": float(row[2]) / 100.0 if row[2] else 0.0,
            "rentabilidade_historica": float(row[3]) if row[3] else 0.0,
            "sharpe": float(row[4]) if row[4] else 0.0,
            "beta": float(row[5]) if row[5] else 0.0,
            "volatilidade": float(row[6]) if row[6] else 0.0
        }

    def get_top_positions(self, session: Session) -> Dict[str, Any]:
        query = text("""
            SELECT a.ticker, v.market_value
            FROM asset_valuations v
            JOIN assets a ON a.id = v.asset_id
            WHERE v.price_date = (SELECT MAX(price_date) FROM asset_valuations)
              AND v.market_value > 0
            ORDER BY v.market_value DESC
        """)
        rows = session.execute(query).fetchall()
        if not rows:
            return {"maior_posicao": None, "menor_posicao": None, "top_5": []}
            
        top_5 = [{"ticker": r[0], "value": float(r[1])/100.0} for r in rows[:5]]
        maior = rows[0][0]
        menor = rows[-1][0]
        return {
            "maior_posicao": maior,
            "menor_posicao": menor,
            "top_5": top_5
        }

    def get_latest_macro(self, session: Session) -> Dict[str, Any]:
        query = text("""
            SELECT indicator_name, value, unit
            FROM macro_indicators
            WHERE date = (SELECT MAX(date) FROM macro_indicators)
        """)
        rows = session.execute(query).fetchall()
        result = {}
        for r in rows:
            result[r[0]] = f"{r[1]}{r[2]}"
        return result
