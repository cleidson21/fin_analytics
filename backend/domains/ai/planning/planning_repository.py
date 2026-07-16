import logging
import uuid
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.domains.ai.planning.planning_models import GoalDTO

logger = logging.getLogger(__name__)

class PlanningRepository:
    def ensure_tables_exist(self, session: Session):
        goals_query = text("""
            CREATE TABLE IF NOT EXISTS financial_goals (
                id TEXT PRIMARY KEY,
                goal_name TEXT,
                target_amount REAL,
                current_amount REAL,
                monthly_contribution REAL,
                expected_return REAL,
                target_date TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1
            )
        """)
        simulations_query = text("""
            CREATE TABLE IF NOT EXISTS financial_simulations (
                id TEXT PRIMARY KEY,
                goal_id TEXT,
                simulation_hash TEXT,
                projection_date TEXT,
                projected_value REAL,
                scenario TEXT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        session.execute(goals_query)
        session.execute(simulations_query)
        session.commit()

    def create_goal(self, session: Session, goal: GoalDTO) -> GoalDTO:
        goal_id = goal.id or str(uuid.uuid4())
        q = text("""
            INSERT INTO financial_goals (
                id, goal_name, target_amount, current_amount, 
                monthly_contribution, expected_return, target_date, active
            ) VALUES (
                :id, :name, :target, :current, :monthly, :expected, :target_date, :active
            )
        """)
        session.execute(q, {
            "id": goal_id,
            "name": goal.goal_name,
            "target": goal.target_amount,
            "current": goal.current_amount or 0.0,
            "monthly": goal.monthly_contribution,
            "expected": goal.expected_return,
            "target_date": goal.target_date,
            "active": goal.active
        })
        session.commit()
        goal.id = goal_id
        return goal

    def get_goals(self, session: Session) -> List[GoalDTO]:
        q = text("""
            SELECT id, goal_name, target_amount, current_amount, 
                   monthly_contribution, expected_return, target_date, active
            FROM financial_goals
            WHERE active = 1
        """)
        rows = session.execute(q).fetchall()
        return [
            GoalDTO(
                id=r[0], goal_name=r[1], target_amount=r[2], current_amount=r[3],
                monthly_contribution=r[4], expected_return=r[5], target_date=r[6], active=bool(r[7])
            ) for r in rows
        ]

    def get_goal_by_id(self, session: Session, goal_id: str) -> Optional[GoalDTO]:
        q = text("""
            SELECT id, goal_name, target_amount, current_amount, 
                   monthly_contribution, expected_return, target_date, active
            FROM financial_goals
            WHERE id = :id
        """)
        r = session.execute(q, {"id": goal_id}).fetchone()
        if not r: return None
        return GoalDTO(
            id=r[0], goal_name=r[1], target_amount=r[2], current_amount=r[3],
            monthly_contribution=r[4], expected_return=r[5], target_date=r[6], active=bool(r[7])
        )

    def save_simulation(self, session: Session, goal_id: str, sim_hash: str, year: int, value: float, scenario: str):
        import datetime
        q = text("""
            INSERT INTO financial_simulations (
                id, goal_id, simulation_hash, projection_date, projected_value, scenario
            ) VALUES (
                :id, :goal_id, :sim_hash, :projection_date, :projected_value, :scenario
            )
        """)
        proj_date = (datetime.datetime.now() + datetime.timedelta(days=365*year)).isoformat()
        session.execute(q, {
            "id": str(uuid.uuid4()),
            "goal_id": goal_id,
            "sim_hash": sim_hash,
            "projection_date": proj_date,
            "projected_value": value,
            "scenario": scenario
        })
        session.commit()

    def get_portfolio_context(self, session: Session) -> Dict[str, Any]:
        # Fetch current equity and dividends history
        q = text("""
            SELECT date, total_equity, dividends_year, dividends_total
            FROM portfolio_snapshots
            ORDER BY date DESC
            LIMIT 1
        """)
        r = session.execute(q).fetchone()
        if not r:
            return {"equity": 0.0, "dividends_year": 0.0, "snapshot_date": "1970-01-01"}
            
        equity = float(r[1] or 0) / 100.0
        dividends_year = float(r[2] or 0) / 100.0
        return {
            "equity": equity,
            "dividends_year": dividends_year,
            "snapshot_date": str(r[0])[:10]
        }

    def get_macro_context(self, session: Session) -> Dict[str, Any]:
        q = text("""
            SELECT indicator_name, value, unit
            FROM macro_indicators
            WHERE date = (SELECT MAX(date) FROM macro_indicators)
        """)
        rows = session.execute(q).fetchall()
        return {r[0]: f"{r[1]}{r[2]}" for r in rows}
