import logging
import uuid
import json
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.ai.executive.executive_models import ExecutiveBriefRecord

logger = logging.getLogger(__name__)

class ExecutiveRepository:
    def ensure_table_exists(self, session: Session):
        query = text("""
            CREATE TABLE IF NOT EXISTS executive_briefs (
                id TEXT PRIMARY KEY,
                brief_date TEXT,
                summary TEXT,
                portfolio_summary TEXT,
                market_summary TEXT,
                insights_summary TEXT,
                planning_summary TEXT,
                risk_summary TEXT,
                recommended_focus TEXT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                cache_key TEXT
            )
        """)
        session.execute(query)
        session.commit()

    def get_context(self, session: Session) -> Dict[str, Any]:
        context = {}
        
        # Portfolio
        q_port = text("""
            SELECT date, total_equity, dividends_total, dividends_year 
            FROM portfolio_snapshots 
            ORDER BY date DESC LIMIT 1
        """)
        r_port = session.execute(q_port).fetchone()
        if r_port:
            context["portfolio"] = {
                "snapshot_date": str(r_port[0])[:10],
                "equity": float(r_port[1] or 0) / 100.0,
                "dividends_total": float(r_port[2] or 0) / 100.0,
                "dividends_year": float(r_port[3] or 0) / 100.0
            }
        else:
            context["portfolio"] = {"snapshot_date": "1970-01-01", "equity": 0.0, "dividends_total": 0.0, "dividends_year": 0.0}

        # Allocation
        q_alloc = text("""
            SELECT a.type, SUM(v.market_value)
            FROM asset_valuations v
            JOIN assets a ON a.id = v.asset_id
            WHERE v.price_date = (SELECT MAX(price_date) FROM asset_valuations)
            GROUP BY a.type
        """)
        rows_alloc = session.execute(q_alloc).fetchall()
        total = sum(float(r[1] or 0) for r in rows_alloc)
        alloc = {str(r[0]): round((float(r[1] or 0) / total) * 100, 2) for r in rows_alloc} if total > 0 else {}
        context["portfolio"]["allocation"] = alloc

        # Macro
        q_macro = text("""
            SELECT indicator_name, value, unit, date
            FROM macro_indicators
            WHERE date = (SELECT MAX(date) FROM macro_indicators)
        """)
        rows_macro = session.execute(q_macro).fetchall()
        macro_date = "1970-01-01"
        macro_data = {}
        for r in rows_macro:
            macro_data[r[0]] = f"{r[1]}{r[2]}"
            macro_date = str(r[3])[:10]
        context["macro"] = macro_data
        context["macro_date"] = macro_date

        # Insights
        q_ins = text("""
            SELECT id, title, severity 
            FROM ai_insights 
            WHERE dismissed = 0 
            ORDER BY generated_at DESC LIMIT 5
        """)
        rows_ins = session.execute(q_ins).fetchall()
        context["insights"] = [{"title": r[1], "severity": r[2]} for r in rows_ins]
        insight_hash = hashlib.md5(json.dumps([r[0] for r in rows_ins]).encode('utf-8')).hexdigest()
        
        # Planning
        q_plan = text("""
            SELECT s.goal_id, g.goal_name, s.scenario, s.projected_value, s.projection_date
            FROM financial_simulations s
            JOIN financial_goals g ON s.goal_id = g.id
            ORDER BY s.generated_at DESC LIMIT 5
        """)
        rows_plan = session.execute(q_plan).fetchall()
        context["planning"] = [{"goal": r[1], "scenario": r[2], "projected": r[3], "date": r[4]} for r in rows_plan]
        planning_hash = hashlib.md5(json.dumps([f"{r[0]}{r[2]}" for r in rows_plan]).encode('utf-8')).hexdigest()
        
        # Cache key composed
        context["cache_key"] = f"{context['portfolio']['snapshot_date']}|{macro_date}|{insight_hash}|{planning_hash}"
        return context

    def get_latest_brief(self, session: Session) -> Optional[ExecutiveBriefRecord]:
        q = text("""
            SELECT id, brief_date, summary, portfolio_summary, market_summary, 
                   insights_summary, planning_summary, risk_summary, recommended_focus, 
                   generated_at, expires_at, cache_key
            FROM executive_briefs
            ORDER BY generated_at DESC
            LIMIT 1
        """)
        r = session.execute(q).fetchone()
        if not r: return None
        return ExecutiveBriefRecord(
            id=r[0], brief_date=r[1], summary=r[2], portfolio_summary=r[3],
            market_summary=r[4], insights_summary=r[5], planning_summary=r[6],
            risk_summary=r[7], recommended_focus=r[8], generated_at=r[9],
            expires_at=r[10], cache_key=r[11]
        )

    def save_brief(self, session: Session, brief: ExecutiveBriefRecord):
        q = text("""
            INSERT INTO executive_briefs (
                id, brief_date, summary, portfolio_summary, market_summary, 
                insights_summary, planning_summary, risk_summary, recommended_focus, 
                generated_at, expires_at, cache_key
            ) VALUES (
                :id, :brief_date, :summary, :portfolio_summary, :market_summary, 
                :insights_summary, :planning_summary, :risk_summary, :recommended_focus, 
                :generated_at, :expires_at, :cache_key
            )
        """)
        session.execute(q, brief.model_dump())
        session.commit()
