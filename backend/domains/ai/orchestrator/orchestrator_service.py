import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.domains.ai.orchestrator.orchestrator_models import OrchestratorStatusDTO, UnifiedContextDTO
from backend.domains.ai.orchestrator.orchestrator_repository import OrchestratorRepository

logger = logging.getLogger(__name__)

class AIOrchestratorService:
    def __init__(self, repository: OrchestratorRepository):
        self.repository = repository

    def get_orchestrator_status(self, session: Session) -> OrchestratorStatusDTO:
        context = self.repository.get_unified_context(session)
        
        modules_status = {
            "advisor": "ok", # Stateless
            "insights": "ok" if context.get("insights") else "missing",
            "planning": "ok" if context.get("planning") else "missing",
            "executive": "ok" if context.get("executive") else "missing",
            "profile": "ok" if context.get("profile") else "missing",
            "coach": "ok" if context.get("coach") else "missing",
            "memory": "ok" if context.get("memory") else "missing",
            "personalization": "ok" if context.get("personalization") else "missing"
        }
        
        all_ok = all(status == "ok" for status in modules_status.values())
        overall_status = "healthy" if all_ok else "degraded"
        
        return OrchestratorStatusDTO(
            status=overall_status,
            modules=modules_status,
            generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

    def get_unified_context(self, session: Session) -> UnifiedContextDTO:
        context = self.repository.get_unified_context(session)
        
        return UnifiedContextDTO(
            profile=context.get("profile"),
            coach=context.get("coach"),
            executive=context.get("executive"),
            personalization=context.get("personalization"),
            memory=context.get("memory"),
            insights=context.get("insights"),
            planning=context.get("planning"),
            advisor_status=context.get("advisor_status"),
            cache_key=context.get("cache_key")
        )
