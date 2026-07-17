import logging
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.domains.ai.orchestrator.orchestrator_service import AIOrchestratorService
from backend.domains.ai.orchestrator.orchestrator_repository import OrchestratorRepository

logger = logging.getLogger(__name__)

class DashboardRepository:
    def __init__(self):
        # Instead of reinventing, we reuse the Orchestrator, as it already consolidates the AI modules.
        # However, to maintain pure Read Model architecture, we fetch it via the service.
        pass

    def get_orchestrator_context(self, session: Session) -> Dict[str, Any]:
        """Fetches the unified context from Orchestrator"""
        repo = OrchestratorRepository()
        svc = AIOrchestratorService(repo)
        ctx = svc.get_unified_context(session)
        status = svc.get_orchestrator_status(session)
        
        return {
            "context": {
                "profile": ctx.profile or {},
                "coach": ctx.coach or {},
                "executive": ctx.executive or {},
                "personalization": ctx.personalization or {},
                "memory": ctx.memory or {},
                "insights": ctx.insights or {},
                "planning": ctx.planning or {}
            },
            "status": status.status,
            "cache_key": ctx.cache_key
        }
