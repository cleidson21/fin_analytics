import logging
import uuid
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.shared.db import engine
from backend.domains.ai.workflow.workflow_repository import WorkflowRepository
from backend.domains.ai.workflow.workflow_models import WorkflowRunRecord, WorkflowStatusDTO
from backend.domains.ai.events.event_models import Event
from backend.domains.ai.events.event_bus import event_bus

# Domain services imports (Decoupled, we just invoke them)
from backend.domains.market_data.router import get_market_data_scheduler, get_macro_indicators_service

from backend.domains.ai.insights.insight_service import AIInsightService
from backend.domains.ai.insights.insight_repository import InsightRepository
from backend.domains.ai.providers.gemini_provider import GeminiProvider

from backend.domains.ai.executive.executive_service import AIExecutiveService
from backend.domains.ai.executive.executive_repository import ExecutiveRepository

from backend.domains.ai.orchestrator.orchestrator_service import AIOrchestratorService
from backend.domains.ai.orchestrator.orchestrator_repository import OrchestratorRepository

from backend.domains.ai.profile.profile_service import AIProfileService
from backend.domains.ai.profile.profile_repository import ProfileRepository

from backend.domains.ai.coach.coach_service import AICoachService
from backend.domains.ai.coach.coach_repository import CoachRepository

from backend.domains.ai.memory.memory_service import AIMemoryService
from backend.domains.ai.memory.memory_repository import MemoryRepository

from backend.domains.ai.personalization.personalization_service import AIPersonalizationService
from backend.domains.ai.personalization.personalization_repository import PersonalizationRepository

logger = logging.getLogger(__name__)

class WorkflowService:
    STEP_EVENTS = {
        "Market Data": "MarketDataUpdated",
        "Macro Indicators": "MacroIndicatorsUpdated",
        "Insights": "InsightsGenerated",
        "Executive Brief": "ExecutiveBriefGenerated",
        "Profile": "ProfileUpdated",
        "Coach": "CoachUpdated",
        "Memory": "MemoryUpdated",
        "Personalization": "PersonalizationUpdated"
    }

    def __init__(self, repository: WorkflowRepository):
        self.repository = repository
        self._is_running = False

    def _get_time(self):
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _execute_pipeline(self, workflow_name: str, workflow_type: str, steps: list, trigger: str):
        if self._is_running:
            logger.warning(f"Workflow {workflow_name} skipped because another workflow is already running.")
            return

        self._is_running = True
        record = WorkflowRunRecord(
            id=str(uuid.uuid4()),
            workflow_name=workflow_name,
            workflow_type=workflow_type,
            status="RUNNING",
            started_at=self._get_time(),
            trigger=trigger,
            executed_steps=""
        )
        
        start_ms = time.time() * 1000
        
        db_session = Session(engine)
        self.repository.create_run(db_session, record)
        
        executed = []
        try:
            for step_name, step_func in steps:
                logger.info(f"Executing Workflow Step: {step_name}")
                step_func(db_session)
                executed.append(step_name)
                record.executed_steps = ",".join(executed)
                self.repository.update_run(db_session, record)
                
                event_type = self.STEP_EVENTS.get(step_name)
                if event_type:
                    event_bus.publish(Event(
                        event_type=event_type,
                        source="WorkflowEngine",
                        payload={"workflow_id": record.id, "trigger": trigger}
                    ))
                
            record.status = "SUCCESS"
            event_bus.publish(Event(
                event_type="WorkflowCompleted",
                source="WorkflowEngine",
                payload={"workflow_id": record.id, "workflow_type": workflow_type, "trigger": trigger}
            ))
        except Exception as e:
            logger.error(f"Workflow {workflow_name} failed at step {step_name}: {str(e)}", exc_info=True)
            record.status = "FAILED"
            record.failed_step = step_name
            record.error_message = str(e)
        finally:
            end_ms = time.time() * 1000
            record.finished_at = self._get_time()
            record.duration_ms = int(end_ms - start_ms)
            self.repository.update_run(db_session, record)
            db_session.close()
            self._is_running = False

    def get_status(self, session: Session) -> WorkflowStatusDTO:
        return WorkflowStatusDTO(
            daily=self.repository.get_last_run_status(session, "daily"),
            weekly=self.repository.get_last_run_status(session, "weekly"),
            monthly=self.repository.get_last_run_status(session, "monthly"),
            last_execution=self.repository.get_last_execution_time(session),
            running=self._is_running
        )

    # --- Steps ---
    def _step_market_data(self, session: Session):
        scheduler = get_market_data_scheduler()
        svc = scheduler.service
        svc.update_market_data(session)

    def _step_macro_indicators(self, session: Session):
        svc = get_macro_indicators_service()
        svc.update_indicators(session)

    def _step_insights(self, session: Session):
        svc = AIInsightService(GeminiProvider(), InsightRepository())
        svc.generate_proactive_insights(session)

    def _step_executive_brief(self, session: Session):
        svc = AIExecutiveService(GeminiProvider(), ExecutiveRepository())
        svc.generate_executive_brief(session)

    def _step_orchestrator(self, session: Session):
        svc = AIOrchestratorService(OrchestratorRepository())
        svc.get_unified_context(session)

    def _step_profile(self, session: Session):
        svc = AIProfileService(GeminiProvider(), ProfileRepository())
        svc.generate_financial_profile(session)

    def _step_coach(self, session: Session):
        svc = AICoachService(GeminiProvider(), CoachRepository())
        svc.generate_coach_plan(session)

    def _step_memory(self, session: Session):
        svc = AIMemoryService(GeminiProvider(), MemoryRepository())
        svc.generate_memory(session)

    def _step_personalization(self, session: Session):
        svc = AIPersonalizationService(GeminiProvider(), PersonalizationRepository())
        svc.generate_personalization(session)

    # --- Workflows ---
    def run_daily(self, trigger="scheduler"):
        steps = [
            ("Market Data", self._step_market_data),
            ("Macro Indicators", self._step_macro_indicators),
            ("Insights", self._step_insights),
            ("Executive Brief", self._step_executive_brief),
            ("Orchestrator", self._step_orchestrator)
        ]
        self._execute_pipeline("daily", "pipeline", steps, trigger)

    def run_weekly(self, trigger="scheduler"):
        steps = [
            ("Profile", self._step_profile),
            ("Coach", self._step_coach)
        ]
        self._execute_pipeline("weekly", "pipeline", steps, trigger)

    def run_monthly(self, trigger="scheduler"):
        steps = [
            ("Memory", self._step_memory),
            ("Personalization", self._step_personalization)
        ]
        self._execute_pipeline("monthly", "pipeline", steps, trigger)
