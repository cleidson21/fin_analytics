import logging
import uuid
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.ai.insights.insight_models import InsightDTO

logger = logging.getLogger(__name__)

class InsightRepository:
    def ensure_table_exists(self, session: Session):
        query = text("""
            CREATE TABLE IF NOT EXISTS ai_insights (
                id TEXT PRIMARY KEY,
                insight_type TEXT,
                severity TEXT,
                title TEXT,
                description TEXT,
                recommendation TEXT,
                source_tables TEXT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                dismissed BOOLEAN DEFAULT 0,
                cache_key TEXT
            )
        """)
        session.execute(query)
        session.commit()

    def get_latest_context_dates(self, session: Session) -> Dict[str, str]:
        # Fetch max dates for cache_key logic
        snapshot_q = text("SELECT MAX(date) FROM portfolio_snapshots")
        macro_q = text("SELECT MAX(date) FROM macro_indicators")
        
        snap_date = session.execute(snapshot_q).scalar() or "1970-01-01"
        macro_date = session.execute(macro_q).scalar() or "1970-01-01"
        
        return {
            "snapshot_date": str(snap_date)[:10],
            "macro_date": str(macro_date)[:10]
        }

    def has_insights_for_cache(self, session: Session, cache_key: str) -> bool:
        q = text("SELECT COUNT(*) FROM ai_insights WHERE cache_key = :cache_key")
        count = session.execute(q, {"cache_key": cache_key}).scalar()
        return count > 0

    def get_active_insights(self, session: Session) -> List[InsightDTO]:
        q = text("""
            SELECT id, insight_type, severity, title, description, recommendation, 
                   source_tables, generated_at, expires_at, dismissed
            FROM ai_insights
            WHERE dismissed = 0
            ORDER BY generated_at DESC
            LIMIT 50
        """)
        rows = session.execute(q).fetchall()
        
        insights = []
        for r in rows:
            sources = json.loads(r[6]) if r[6] else []
            insights.append(InsightDTO(
                id=r[0],
                insight_type=r[1],
                severity=r[2],
                title=r[3],
                description=r[4],
                recommendation=r[5],
                source_tables=sources,
                generated_at=r[7],
                expires_at=r[8],
                dismissed=bool(r[9])
            ))
        return insights

    def save_insights(self, session: Session, insights: List[InsightDTO], cache_key: str):
        q = text("""
            INSERT INTO ai_insights (
                id, insight_type, severity, title, description, recommendation, 
                source_tables, generated_at, expires_at, dismissed, cache_key
            ) VALUES (
                :id, :insight_type, :severity, :title, :description, :recommendation,
                :source_tables, :generated_at, :expires_at, :dismissed, :cache_key
            )
        """)
        for ins in insights:
            session.execute(q, {
                "id": ins.id or str(uuid.uuid4()),
                "insight_type": ins.insight_type,
                "severity": ins.severity,
                "title": ins.title,
                "description": ins.description,
                "recommendation": ins.recommendation,
                "source_tables": json.dumps(ins.source_tables),
                "generated_at": ins.generated_at,
                "expires_at": ins.expires_at,
                "dismissed": 0,
                "cache_key": cache_key
            })
        session.commit()

    def get_portfolio_summary(self, session: Session) -> List[Dict[str, Any]]:
        # Fetch last 3 months of snapshots to detect growth/falls
        q = text("""
            SELECT date, total_equity, dividends_total
            FROM portfolio_snapshots
            ORDER BY date DESC
            LIMIT 3
        """)
        rows = session.execute(q).fetchall()
        return [{"date": str(r[0]), "equity": float(r[1] or 0)/100.0, "dividends": float(r[2] or 0)/100.0} for r in rows]

    def get_allocation_summary(self, session: Session) -> Dict[str, Any]:
        q = text("""
            SELECT a.type, SUM(v.market_value)
            FROM asset_valuations v
            JOIN assets a ON a.id = v.asset_id
            WHERE v.price_date = (SELECT MAX(price_date) FROM asset_valuations)
            GROUP BY a.type
        """)
        rows = session.execute(q).fetchall()
        total = sum(float(r[1] or 0) for r in rows)
        if total == 0: return {}
        return {str(r[0]): round((float(r[1] or 0) / total) * 100, 2) for r in rows}

    def get_macro_summary(self, session: Session) -> Dict[str, Any]:
        q = text("""
            SELECT indicator_name, value, unit
            FROM macro_indicators
            WHERE date = (SELECT MAX(date) FROM macro_indicators)
        """)
        rows = session.execute(q).fetchall()
        return {r[0]: f"{r[1]}{r[2]}" for r in rows}
