import logging
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from backend.shared.db import engine
from backend.domains.ai.coach.coach_service import AICoachService

logger = logging.getLogger(__name__)

class CoachScheduler:
    def __init__(self, service: AICoachService):
        self.service = service
        self._scheduler = BackgroundScheduler()

    def start(self):
        logger.info("Starting CoachScheduler (Weekly)...")
        # Run weekly on Sunday at 05:00 AM (after Profile which runs at 04:00)
        self._scheduler.add_job(
            self.run_coach_sync,
            'cron',
            day_of_week='sun',
            hour=5, 
            minute=0,
            id='financial_coach_sync'
        )
        self._scheduler.start()
        
        # Ensure it runs at least once on startup if not present
        self._scheduler.add_job(self.run_coach_sync, 'date', id='startup_coach_sync')

    def stop(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("CoachScheduler stopped.")

    def run_coach_sync(self):
        logger.info("--- AI FINANCIAL COACH PLAN GENERATION STARTED ---")
        db_session = Session(engine)
        try:
            coach_plan = self.service.generate_coach_plan(db_session)
            if coach_plan:
                logger.info(f"Generated new Financial Coach Plan (Version {coach_plan.coach_version}).")
            else:
                logger.info("Financial Coach Plan generation skipped or failed.")
        except Exception as e:
            logger.error(f"Error during AI Financial Coach Plan Generation: {str(e)}", exc_info=True)
        finally:
            db_session.close()
            logger.info("--- AI FINANCIAL COACH PLAN GENERATION ENDED ---")
