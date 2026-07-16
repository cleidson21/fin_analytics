import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

class MacroIndicatorsRepository:
    def save_indicators(self, session: Session, indicators: List[Dict[str, Any]]) -> int:
        """
        Salva os indicadores (CDI, SELIC, IPCA) no banco.
        indicators dict: {"indicator_type": "CDI", "date": "2023-01-01", "value": 13.65}
        """
        count = 0
        for ind in indicators:
            record_id = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO macro_indicators (id, indicator_type, date, value)
                    VALUES (:id, :type, :date, :value)
                    ON CONFLICT(indicator_type, date) DO UPDATE SET
                        value = excluded.value,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {
                    "id": record_id,
                    "type": ind["indicator_type"],
                    "date": ind["date"],
                    "value": float(ind["value"])
                }
            )
            count += 1
        return count

    def get_latest_indicators(self, session: Session) -> List[Dict[str, Any]]:
        """Busca o valor mais recente para cada indicador"""
        result = session.execute(
            text("""
                SELECT indicator_type, date, value
                FROM (
                    SELECT indicator_type, date, value,
                           ROW_NUMBER() OVER(PARTITION BY indicator_type ORDER BY date DESC) as rn
                    FROM macro_indicators
                ) tmp
                WHERE rn = 1
            """)
        ).fetchall()
        
        return [
            {
                "indicator_type": row[0],
                "date": row[1],
                "value": row[2]
            }
            for row in result
        ]

    def get_historical_indicators(self, session: Session, indicator_type: str = None) -> List[Dict[str, Any]]:
        """Busca o histórico de indicadores, opcionalmente filtrado por tipo"""
        query = "SELECT indicator_type, date, value FROM macro_indicators"
        params = {}
        if indicator_type:
            query += " WHERE indicator_type = :type"
            params["type"] = indicator_type
            
        query += " ORDER BY date DESC"
        
        result = session.execute(text(query), params).fetchall()
        
        return [
            {
                "indicator_type": row[0],
                "date": row[1],
                "value": row[2]
            }
            for row in result
        ]
