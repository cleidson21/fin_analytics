import logging
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from backend.shared.db import engine
from backend.domains.ai.executive.executive_service import AIExecutiveService

logger = logging.getLogger(__name__)

class ExecutiveScheduler:
    def __init__(self, service: AIExecutiveService):
        self.service = service
        self._scheduler = BackgroundScheduler()

    def start(self):
        logger.info("Starting ExecutiveScheduler (Daily)...")
        # Run at 03:00 AM, conceptually after Insights (02:00) and Market Data
        self._scheduler.add_job(
            self.run_executive_sync,
            'cron',
            hour=3, 
            minute=0,
            id='executive_brief_sync'
        )
        self._scheduler.start()
        
        # Also run at startup to guarantee brief is available
        self._scheduler.add_job(self.run_executive_sync, 'date', id='startup_executive_sync')

    def stop(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("ExecutiveScheduler stopped.")

    def run_executive_sync(self):
        logger.info("--- AI EXECUTIVE BRIEF GENERATION STARTED ---")
        db_session = Session(engine)
        try:
            brief = self.service.generate_executive_brief(db_session)
            if brief:
                logger.info(f"Generated new Executive Brief for {brief.brief_date}.")
            else:
                logger.info("Executive Brief generation skipped or failed.")
        except Exception as e:
            logger.error(f"Error during AI Executive Brief Generation: {str(e)}", exc_info=True)
        finally:
            db_session.close()
            logger.info("--- AI EXECUTIVE BRIEF GENERATION ENDED ---")
