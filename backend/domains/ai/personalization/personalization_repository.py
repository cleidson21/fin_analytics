import logging
import uuid
import json
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.ai.personalization.personalization_models import PersonalizationRecord

logger = logging.getLogger(__name__)

class PersonalizationRepository:
    def ensure_table_exists(self, session: Session):
        query = text("""
            CREATE TABLE IF NOT EXISTS ai_personalization (
                id TEXT PRIMARY KEY,
                personalization_version INTEGER,
                communication_style TEXT,
                detail_level TEXT,
                priority_topics TEXT,
                preferred_frequency TEXT,
                dashboard_focus TEXT,
                notification_preferences TEXT,
                learning_preferences TEXT,
                language_profile TEXT,
                summary_preferences TEXT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                cache_key TEXT
            )
        """)
        session.execute(query)
        session.commit()

    def get_context(self, session: Session) -> Dict[str, Any]:
        context = {}
        
        # Memory
        q_mem = text("""
            SELECT id, investment_preferences, behavior_patterns, recurring_goals, learning_summary
            FROM financial_memory
            ORDER BY generated_at DESC LIMIT 1
        """)
        r_mem = session.execute(q_mem).fetchone()
        memory_hash = "no_memory"
        if r_mem:
            context["memory"] = {
                "investment_preferences": r_mem[1],
                "behavior_patterns": r_mem[2],
                "recurring_goals": r_mem[3],
                "learning_summary": r_mem[4]
            }
            memory_hash = hashlib.md5(str(r_mem[0]).encode('utf-8')).hexdigest()
        else:
            context["memory"] = {}

        # Profile
        q_prof = text("""
            SELECT id, investor_profile, investment_style, behavior_summary
            FROM financial_profile
            ORDER BY generated_at DESC LIMIT 1
        """)
        r_prof = session.execute(q_prof).fetchone()
        profile_hash = "no_profile"
        if r_prof:
            context["profile"] = {
                "investor_profile": r_prof[1],
                "investment_style": r_prof[2],
                "behavior_summary": r_prof[3]
            }
            profile_hash = hashlib.md5(str(r_prof[0]).encode('utf-8')).hexdigest()
        else:
            context["profile"] = {}

        # Coach
        q_coach = text("""
            SELECT id, weekly_focus, monthly_focus, recommended_habits
            FROM financial_coaching
            ORDER BY generated_at DESC LIMIT 1
        """)
        r_coach = session.execute(q_coach).fetchone()
        coach_hash = "no_coach"
        if r_coach:
            context["coach"] = {
                "weekly_focus": r_coach[1],
                "monthly_focus": r_coach[2],
                "recommended_habits": r_coach[3]
            }
            coach_hash = hashlib.md5(str(r_coach[0]).encode('utf-8')).hexdigest()
        else:
            context["coach"] = {}

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

        # Insights
        q_ins = text("""
            SELECT id, title, severity 
            FROM ai_insights 
            WHERE dismissed = 0 
            ORDER BY generated_at DESC LIMIT 5
        """)
        rows_ins = session.execute(q_ins).fetchall()
        context["insights"] = [{"title": r[1], "severity": r[2]} for r in rows_ins]

        context["cache_key"] = f"{memory_hash}|{profile_hash}|{coach_hash}|{brief_hash}"
        return context

    def get_latest_personalization(self, session: Session) -> Optional[PersonalizationRecord]:
        q = text("""
            SELECT id, personalization_version, communication_style, detail_level,
                   priority_topics, preferred_frequency, dashboard_focus,
                   notification_preferences, learning_preferences, language_profile,
                   summary_preferences, generated_at, expires_at, cache_key
            FROM ai_personalization
            ORDER BY generated_at DESC
            LIMIT 1
        """)
        r = session.execute(q).fetchone()
        if not r: return None
        return PersonalizationRecord(
            id=r[0], personalization_version=r[1], communication_style=r[2],
            detail_level=r[3], priority_topics=r[4], preferred_frequency=r[5],
            dashboard_focus=r[6], notification_preferences=r[7],
            learning_preferences=r[8], language_profile=r[9],
            summary_preferences=r[10], generated_at=r[11], expires_at=r[12],
            cache_key=r[13]
        )

    def save_personalization(self, session: Session, record: PersonalizationRecord):
        q = text("""
            INSERT INTO ai_personalization (
                id, personalization_version, communication_style, detail_level,
                priority_topics, preferred_frequency, dashboard_focus,
                notification_preferences, learning_preferences, language_profile,
                summary_preferences, generated_at, expires_at, cache_key
            ) VALUES (
                :id, :personalization_version, :communication_style, :detail_level,
                :priority_topics, :preferred_frequency, :dashboard_focus,
                :notification_preferences, :learning_preferences, :language_profile,
                :summary_preferences, :generated_at, :expires_at, :cache_key
            )
        """)
        session.execute(q, record.model_dump())
        session.commit()
