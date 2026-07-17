import logging
import uuid
import json
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.ai.memory.memory_models import MemoryRecord

logger = logging.getLogger(__name__)

class MemoryRepository:
    def ensure_table_exists(self, session: Session):
        query = text("""
            CREATE TABLE IF NOT EXISTS financial_memory (
                id TEXT PRIMARY KEY,
                memory_version INTEGER,
                investment_preferences TEXT,
                behavior_patterns TEXT,
                historical_strengths TEXT,
                historical_attention_points TEXT,
                recurring_goals TEXT,
                learning_summary TEXT,
                confidence_score REAL,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                cache_key TEXT
            )
        """)
        session.execute(query)
        session.commit()

    def get_context(self, session: Session) -> Dict[str, Any]:
        context = {}
        
        # Profile History (Last 4 versions)
        q_prof = text("""
            SELECT id, investor_profile, investment_style, behavior_summary, generated_at
            FROM financial_profile
            ORDER BY generated_at DESC LIMIT 4
        """)
        rows_prof = session.execute(q_prof).fetchall()
        context["profile_history"] = [{"profile": r[1], "style": r[2], "summary": r[3], "date": str(r[4])} for r in rows_prof]
        profile_hash = hashlib.md5(json.dumps([r[0] for r in rows_prof]).encode('utf-8')).hexdigest()

        # Coach History (Last 4 plans)
        q_coach = text("""
            SELECT id, weekly_focus, monthly_focus, recommended_habits, generated_at
            FROM financial_coaching
            ORDER BY generated_at DESC LIMIT 4
        """)
        rows_coach = session.execute(q_coach).fetchall()
        context["coach_history"] = [{"week": r[1], "month": r[2], "habits": r[3], "date": str(r[4])} for r in rows_coach]
        coach_hash = hashlib.md5(json.dumps([r[0] for r in rows_coach]).encode('utf-8')).hexdigest()

        # Executive Briefs (Last 10 to see evolution)
        q_brief = text("""
            SELECT id, summary, recommended_focus
            FROM executive_briefs
            ORDER BY generated_at DESC LIMIT 10
        """)
        rows_brief = session.execute(q_brief).fetchall()
        context["executive_history"] = [{"summary": r[1], "focus": r[2]} for r in rows_brief]
        brief_hash = hashlib.md5(json.dumps([r[0] for r in rows_brief]).encode('utf-8')).hexdigest()

        # Planning
        q_plan = text("""
            SELECT s.goal_id, g.goal_name, s.scenario, s.generated_at
            FROM financial_simulations s
            JOIN financial_goals g ON s.goal_id = g.id
            ORDER BY s.generated_at DESC LIMIT 10
        """)
        rows_plan = session.execute(q_plan).fetchall()
        context["planning_history"] = [{"goal": r[1], "scenario": r[2], "date": str(r[3])} for r in rows_plan]
        planning_hash = hashlib.md5(json.dumps([f"{r[0]}{r[2]}" for r in rows_plan]).encode('utf-8')).hexdigest()

        # Snapshot extremes (To know overall time span)
        q_port = text("""
            SELECT MIN(date), MAX(date)
            FROM portfolio_snapshots 
        """)
        r_port = session.execute(q_port).fetchone()
        context["portfolio_summary"] = {
            "first_snapshot": str(r_port[0])[:10] if r_port and r_port[0] else "N/A",
            "last_snapshot": str(r_port[1])[:10] if r_port and r_port[1] else "N/A"
        }

        context["cache_key"] = f"{profile_hash}|{coach_hash}|{brief_hash}|{planning_hash}"
        return context

    def get_latest_memory(self, session: Session) -> Optional[MemoryRecord]:
        q = text("""
            SELECT id, memory_version, investment_preferences, behavior_patterns,
                   historical_strengths, historical_attention_points, recurring_goals,
                   learning_summary, confidence_score, generated_at, expires_at, cache_key
            FROM financial_memory
            ORDER BY generated_at DESC
            LIMIT 1
        """)
        r = session.execute(q).fetchone()
        if not r: return None
        return MemoryRecord(
            id=r[0], memory_version=r[1], investment_preferences=r[2],
            behavior_patterns=r[3], historical_strengths=r[4],
            historical_attention_points=r[5], recurring_goals=r[6],
            learning_summary=r[7], confidence_score=r[8],
            generated_at=r[9], expires_at=r[10], cache_key=r[11]
        )

    def save_memory(self, session: Session, record: MemoryRecord):
        q = text("""
            INSERT INTO financial_memory (
                id, memory_version, investment_preferences, behavior_patterns,
                historical_strengths, historical_attention_points, recurring_goals,
                learning_summary, confidence_score, generated_at, expires_at, cache_key
            ) VALUES (
                :id, :memory_version, :investment_preferences, :behavior_patterns,
                :historical_strengths, :historical_attention_points, :recurring_goals,
                :learning_summary, :confidence_score, :generated_at, :expires_at, :cache_key
            )
        """)
        session.execute(q, record.model_dump())
        session.commit()
