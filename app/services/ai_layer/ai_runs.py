from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ai_layer import AiRun
from datetime import datetime
import uuid
from typing import Dict, Any

class AIRunService:
    def __init__(self, db: Session):
        self.db = db

    def register_run(
        self, 
        prompt_version_id: str, 
        import_run_id: str, 
        model: str, 
        input_text: str, 
        tokens_input: int, 
        tokens_output: int, 
        estimated_cost: float,
        status: str = 'SUCCESS'
    ) -> AiRun:
        run = AiRun(
            id=str(uuid.uuid4()),
            prompt_version_id=prompt_version_id,
            import_run_id=import_run_id,
            model=model,
            input_text=input_text,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            estimated_cost=estimated_cost,
            status=status,
            created_at=datetime.utcnow()
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_aggregated_report(self) -> Dict[str, Any]:
        """Gera relatórios agregados (ex: total de tokens, custo total)."""
        summary = self.db.query(
            func.sum(AiRun.tokens_input).label("total_tokens_input"),
            func.sum(AiRun.tokens_output).label("total_tokens_output"),
            func.sum(AiRun.estimated_cost).label("total_cost"),
            func.count(AiRun.id).label("total_runs")
        ).first()

        return {
            "total_tokens_input": summary.total_tokens_input or 0,
            "total_tokens_output": summary.total_tokens_output or 0,
            "total_cost": summary.total_cost or 0.0,
            "total_runs": summary.total_runs or 0
        }
