import logging
import hashlib
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class OrchestratorRepository:

    def get_module_latest(self, session: Session, table: str) -> Tuple[Dict[str, Any], str]:
        """Fetch the latest row from a given AI table as a dict and return its hash."""
        try:
            q = text(f"SELECT * FROM {table} ORDER BY generated_at DESC LIMIT 1")
            row = session.execute(q).mappings().fetchone()
            if row:
                row_dict = dict(row)
                row_hash = hashlib.md5(str(row_dict.get('id', '')).encode('utf-8')).hexdigest()
                return row_dict, row_hash
            return {}, "missing"
        except Exception:
            return {}, "error"

    def get_unified_context(self, session: Session) -> Dict[str, Any]:
        
        # Profile
        profile_data, profile_hash = self.get_module_latest(session, "financial_profile")
        
        # Coach
        coach_data, coach_hash = self.get_module_latest(session, "financial_coaching")
        
        # Executive
        executive_data, executive_hash = self.get_module_latest(session, "executive_briefs")
        
        # Memory
        memory_data, memory_hash = self.get_module_latest(session, "financial_memory")
        
        # Personalization
        personalization_data, personalization_hash = self.get_module_latest(session, "ai_personalization")
        
        # Insights (Latest 5 active)
        try:
            q_ins = text("SELECT id, title, severity FROM ai_insights WHERE dismissed = 0 ORDER BY generated_at DESC LIMIT 5")
            rows_ins = session.execute(q_ins).fetchall()
            insights_data = {"active_insights": [{"title": r[1], "severity": r[2]} for r in rows_ins]}
            insights_hash = hashlib.md5(str([r[0] for r in rows_ins]).encode('utf-8')).hexdigest() if rows_ins else "missing"
        except Exception:
            insights_data = {}
            insights_hash = "error"
            
        # Planning (Latest 3)
        try:
            q_plan = text("SELECT id, scenario FROM financial_simulations ORDER BY generated_at DESC LIMIT 3")
            rows_plan = session.execute(q_plan).fetchall()
            planning_data = {"simulations": [{"scenario": r[1]} for r in rows_plan]}
            planning_hash = hashlib.md5(str([r[0] for r in rows_plan]).encode('utf-8')).hexdigest() if rows_plan else "missing"
        except Exception:
            planning_data = {}
            planning_hash = "error"

        # Combine hash
        combined_hash = hashlib.md5(f"{profile_hash}|{coach_hash}|{executive_hash}|{memory_hash}|{personalization_hash}|{insights_hash}|{planning_hash}".encode('utf-8')).hexdigest()
        
        return {
            "profile": profile_data,
            "coach": coach_data,
            "executive": executive_data,
            "personalization": personalization_data,
            "memory": memory_data,
            "insights": insights_data,
            "planning": planning_data,
            "advisor_status": "stateless", # Advisor is on-demand, always available
            "cache_key": combined_hash
        }
