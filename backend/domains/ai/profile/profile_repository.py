import logging
import uuid
import json
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.ai.profile.profile_models import ProfileRecord

logger = logging.getLogger(__name__)

class ProfileRepository:
    def ensure_table_exists(self, session: Session):
        query = text("""
            CREATE TABLE IF NOT EXISTS financial_profile (
                id TEXT PRIMARY KEY,
                profile_version INTEGER,
                investor_profile TEXT,
                risk_tolerance TEXT,
                investment_style TEXT,
                portfolio_maturity TEXT,
                diversification_score TEXT,
                cash_behavior TEXT,
                dividend_focus TEXT,
                consistency_score TEXT,
                planning_score TEXT,
                macro_sensitivity TEXT,
                behavior_summary TEXT,
                strengths TEXT,
                attention_points TEXT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                cache_key TEXT
            )
        """)
        session.execute(query)
        session.commit()

    def get_context(self, session: Session) -> Dict[str, Any]:
        context = {}
        
        # Portfolio (Last 6 months to evaluate consistency)
        q_port = text("""
            SELECT date, total_equity, dividends_total, dividends_year 
            FROM portfolio_snapshots 
            ORDER BY date DESC LIMIT 6
        """)
        rows_port = session.execute(q_port).fetchall()
        if rows_port:
            context["portfolio"] = [
                {"date": str(r[0])[:10], "equity": float(r[1] or 0)/100.0} 
                for r in rows_port
            ]
            snapshot_date = str(rows_port[0][0])[:10]
        else:
            context["portfolio"] = []
            snapshot_date = "1970-01-01"

        # Briefs (Last 4 to evaluate recurrent priorities)
        q_briefs = text("""
            SELECT id, summary, recommended_focus
            FROM executive_briefs
            ORDER BY generated_at DESC LIMIT 4
        """)
        rows_briefs = session.execute(q_briefs).fetchall()
        context["briefs"] = [{"summary": r[1], "focus": r[2]} for r in rows_briefs]
        brief_hash = hashlib.md5(json.dumps([r[0] for r in rows_briefs]).encode('utf-8')).hexdigest()

        # Planning
        q_plan = text("""
            SELECT s.goal_id, g.goal_name, s.scenario
            FROM financial_simulations s
            JOIN financial_goals g ON s.goal_id = g.id
            ORDER BY s.generated_at DESC LIMIT 3
        """)
        rows_plan = session.execute(q_plan).fetchall()
        context["planning"] = [{"goal": r[1], "scenario": r[2]} for r in rows_plan]
        planning_hash = hashlib.md5(json.dumps([f"{r[0]}{r[2]}" for r in rows_plan]).encode('utf-8')).hexdigest()

        # Insights
        q_ins = text("""
            SELECT id, insight_type, title
            FROM ai_insights 
            WHERE dismissed = 0 
            ORDER BY generated_at DESC LIMIT 10
        """)
        rows_ins = session.execute(q_ins).fetchall()
        context["insights"] = [{"type": r[1], "title": r[2]} for r in rows_ins]
        insight_hash = hashlib.md5(json.dumps([r[0] for r in rows_ins]).encode('utf-8')).hexdigest()

        # Macro
        q_macro = text("""
            SELECT indicator_name, value, unit
            FROM macro_indicators
            WHERE date = (SELECT MAX(date) FROM macro_indicators)
        """)
        rows_macro = session.execute(q_macro).fetchall()
        context["macro"] = {r[0]: f"{r[1]}{r[2]}" for r in rows_macro}

        context["cache_key"] = f"{snapshot_date}|{brief_hash}|{planning_hash}|{insight_hash}"
        return context

    def get_latest_profile(self, session: Session) -> Optional[ProfileRecord]:
        q = text("""
            SELECT id, profile_version, investor_profile, risk_tolerance, investment_style,
                   portfolio_maturity, diversification_score, cash_behavior, dividend_focus,
                   consistency_score, planning_score, macro_sensitivity, behavior_summary,
                   strengths, attention_points, generated_at, expires_at, cache_key
            FROM financial_profile
            ORDER BY generated_at DESC
            LIMIT 1
        """)
        r = session.execute(q).fetchone()
        if not r: return None
        return ProfileRecord(
            id=r[0], profile_version=r[1], investor_profile=r[2], risk_tolerance=r[3],
            investment_style=r[4], portfolio_maturity=r[5], diversification_score=r[6],
            cash_behavior=r[7], dividend_focus=r[8], consistency_score=r[9],
            planning_score=r[10], macro_sensitivity=r[11], behavior_summary=r[12],
            strengths=r[13], attention_points=r[14], generated_at=r[15],
            expires_at=r[16], cache_key=r[17]
        )

    def save_profile(self, session: Session, profile: ProfileRecord):
        q = text("""
            INSERT INTO financial_profile (
                id, profile_version, investor_profile, risk_tolerance, investment_style,
                portfolio_maturity, diversification_score, cash_behavior, dividend_focus,
                consistency_score, planning_score, macro_sensitivity, behavior_summary,
                strengths, attention_points, generated_at, expires_at, cache_key
            ) VALUES (
                :id, :profile_version, :investor_profile, :risk_tolerance, :investment_style,
                :portfolio_maturity, :diversification_score, :cash_behavior, :dividend_focus,
                :consistency_score, :planning_score, :macro_sensitivity, :behavior_summary,
                :strengths, :attention_points, :generated_at, :expires_at, :cache_key
            )
        """)
        session.execute(q, profile.model_dump())
        session.commit()
