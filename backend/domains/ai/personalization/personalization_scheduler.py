import logging
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from backend.shared.db import engine
from backend.domains.ai.personalization.personalization_service import AIPersonalizationService

logger = logging.getLogger(__name__)

class PersonalizationScheduler:
    def __init__(self, service: AIPersonalizationService):
        self.service = service
        self._scheduler = BackgroundScheduler()

    def start(self):
        logger.info("Starting PersonalizationScheduler (Monthly)...")
        # Run monthly on the 1st day at 07:00 AM (After memory sync)
        self._scheduler.add_job(
            self.run_personalization_sync,
            'cron',
            day=1,
            hour=7, 
            minute=0,
            id='ai_personalization_sync'
        )
        self._scheduler.start()
        
        # Ensure it runs at least once on startup if not present
        self._scheduler.add_job(self.run_personalization_sync, 'date', id='startup_personalization_sync')

    def stop(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("PersonalizationScheduler stopped.")

    def run_personalization_sync(self):
        logger.info("--- AI PERSONALIZATION GENERATION STARTED ---")
        db_session = Session(engine)
        try:
            pers = self.service.generate_personalization(db_session)
            if pers:
                logger.info(f"Generated new AI Personalization (Version {pers.personalization_version}).")
            else:
                logger.info("AI Personalization generation skipped or failed.")
        except Exception as e:
            logger.error(f"Error during AI Personalization Generation: {str(e)}", exc_info=True)
        finally:
            db_session.close()
            logger.info("--- AI PERSONALIZATION GENERATION ENDED ---")
