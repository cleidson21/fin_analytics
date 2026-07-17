import logging
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.domains.ai.dashboard.dashboard_models import DashboardViewModelDTO
from backend.domains.ai.dashboard.dashboard_repository import DashboardRepository

logger = logging.getLogger(__name__)

class DashboardDeliveryService:
    def __init__(self, repository: DashboardRepository):
        self.repository = repository
        self._cached_payload = None
        self._last_cache_key = None

    def get_dashboard_view_model(self, session: Session) -> DashboardViewModelDTO:
        data = self.repository.get_orchestrator_context(session)
        cache_key = data["cache_key"]
        status = data["status"]
        ctx = data["context"]
        
        # Check Memory Cache
        if self._last_cache_key == cache_key and self._cached_payload:
            logger.info(f"Dashboard Delivery cache hit for {cache_key}. Returning in-memory payload.")
            return self._cached_payload
            
        logger.info(f"Dashboard Delivery cache miss. Rebuilding ViewModel for {cache_key}.")
            
        # Parse Coach Priorities
        coach_raw = ctx.get("coach", {})
        priorities = []
        if coach_raw and "priority_actions" in coach_raw:
            try:
                priorities = json.loads(coach_raw["priority_actions"])
            except:
                pass
                
        # Parse Insights
        insights_raw = ctx.get("insights", {})
        insights_list = insights_raw.get("active_insights", [])
        
        # Parse Executive Brief
        exec_raw = ctx.get("executive", {})
        summary = {
            "text": exec_raw.get("summary", "Resumo indisponível."),
            "focus": exec_raw.get("recommended_focus", "N/A")
        }
        
        # Build ViewModel
        view_model = DashboardViewModelDTO(
            summary=summary,
            portfolio={"status": "consolidated"}, # Placeholder for actual portfolio metrics which would be merged here if we had direct UI mapping
            insights=insights_list,
            priorities=priorities,
            planning=ctx.get("planning", {}),
            coach={
                "weekly_focus": coach_raw.get("weekly_focus", "N/A"),
                "monthly_focus": coach_raw.get("monthly_focus", "N/A")
            },
            profile={
                "investor_profile": ctx.get("profile", {}).get("investor_profile", "Desconhecido"),
                "investment_style": ctx.get("profile", {}).get("investment_style", "N/A")
            },
            personalization=ctx.get("personalization", {}),
            status=status,
            generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            cache_key=cache_key
        )
        
        # Save in memory cache
        self._last_cache_key = cache_key
        self._cached_payload = view_model
        
        return view_model
