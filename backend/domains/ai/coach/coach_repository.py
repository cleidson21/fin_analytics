import logging
import uuid
import json
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.ai.coach.coach_models import CoachRecord

logger = logging.getLogger(__name__)

class CoachRepository:
    def ensure_table_exists(self, session: Session):
        query = text("""
            CREATE TABLE IF NOT EXISTS financial_coaching (
                id TEXT PRIMARY KEY,
                coach_version INTEGER,
                action_plan TEXT,
                weekly_focus TEXT,
                monthly_focus TEXT,
                recommended_habits TEXT,
                priority_actions TEXT,
                portfolio_observations TEXT,
                risk_observations TEXT,
                planning_observations TEXT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                cache_key TEXT
            )
        """)
        session.execute(query)
        session.commit()

    def get_context(self, session: Session) -> Dict[str, Any]:
        context = {}
        
        # Profile
        q_prof = text("""
            SELECT id, investor_profile, investment_style, behavior_summary, strengths, attention_points
            FROM financial_profile
            ORDER BY generated_at DESC LIMIT 1
        """)
        r_prof = session.execute(q_prof).fetchone()
        profile_hash = "no_profile"
        if r_prof:
            context["profile"] = {
                "investor_profile": r_prof[1],
                "investment_style": r_prof[2],
                "behavior_summary": r_prof[3],
                "strengths": r_prof[4],
                "attention_points": r_prof[5]
            }
            profile_hash = hashlib.md5(str(r_prof[0]).encode('utf-8')).hexdigest()
        else:
            context["profile"] = {}

        # Executive Brief
        q_brief = text("""
            SELECT id, summary, recommended_focus
            FROM executive_briefs
            ORDER BY generated_at DESC LIMIT 1
        """)
        r_brief = session.execute(q_brief).fetchone()
        brief_hash = "no_brief"
        if r_brief:
            context["executive"] = {
                "summary": r_brief[1],
                "recommended_focus": r_brief[2]
            }
            brief_hash = hashlib.md5(str(r_brief[0]).encode('utf-8')).hexdigest()
        else:
            context["executive"] = {}

        # Planning
        q_plan = text("""
            SELECT s.goal_id, g.goal_name, s.scenario, s.projected_value
            FROM financial_simulations s
            JOIN financial_goals g ON s.goal_id = g.id
            ORDER BY s.generated_at DESC LIMIT 3
        """)
        rows_plan = session.execute(q_plan).fetchall()
        context["planning"] = [{"goal": r[1], "scenario": r[2], "projected": r[3]} for r in rows_plan]
        planning_hash = hashlib.md5(json.dumps([f"{r[0]}{r[2]}" for r in rows_plan]).encode('utf-8')).hexdigest()

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

        # Macro
        q_macro = text("""
            SELECT indicator_name, value, unit
            FROM macro_indicators
            WHERE date = (SELECT MAX(date) FROM macro_indicators)
        """)
        rows_macro = session.execute(q_macro).fetchall()
        context["macro"] = {r[0]: f"{r[1]}{r[2]}" for r in rows_macro}

        context["cache_key"] = f"{profile_hash}|{brief_hash}|{planning_hash}|{insight_hash}"
        return context

    def get_latest_coach_plan(self, session: Session) -> Optional[CoachRecord]:
        q = text("""
            SELECT id, coach_version, action_plan, weekly_focus, monthly_focus,
                   recommended_habits, priority_actions, portfolio_observations,
                   risk_observations, planning_observations, generated_at, expires_at, cache_key
            FROM financial_coaching
            ORDER BY generated_at DESC
            LIMIT 1
        """)
        r = session.execute(q).fetchone()
        if not r: return None
        return CoachRecord(
            id=r[0], coach_version=r[1], action_plan=r[2], weekly_focus=r[3],
            monthly_focus=r[4], recommended_habits=r[5], priority_actions=r[6],
            portfolio_observations=r[7], risk_observations=r[8],
            planning_observations=r[9], generated_at=r[10], expires_at=r[11], cache_key=r[12]
        )

    def save_coach_plan(self, session: Session, record: CoachRecord):
        q = text("""
            INSERT INTO financial_coaching (
                id, coach_version, action_plan, weekly_focus, monthly_focus,
                recommended_habits, priority_actions, portfolio_observations,
                risk_observations, planning_observations, generated_at, expires_at, cache_key
            ) VALUES (
                :id, :coach_version, :action_plan, :weekly_focus, :monthly_focus,
                :recommended_habits, :priority_actions, :portfolio_observations,
                :risk_observations, :planning_observations, :generated_at, :expires_at, :cache_key
            )
        """)
        session.execute(q, record.model_dump())
        session.commit()
