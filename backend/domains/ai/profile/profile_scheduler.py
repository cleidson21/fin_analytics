import logging
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from backend.shared.db import engine
from backend.domains.ai.profile.profile_service import AIProfileService

logger = logging.getLogger(__name__)

class ProfileScheduler:
    def __init__(self, service: AIProfileService):
        self.service = service
        self._scheduler = BackgroundScheduler()

    def start(self):
        logger.info("Starting ProfileScheduler (Weekly)...")
        # Run weekly on Sunday at 04:00 AM
        self._scheduler.add_job(
            self.run_profile_sync,
            'cron',
            day_of_week='sun',
            hour=4, 
            minute=0,
            id='financial_profile_sync'
        )
        self._scheduler.start()
        
        # Ensure it runs at least once on startup if not present
        self._scheduler.add_job(self.run_profile_sync, 'date', id='startup_profile_sync')

    def stop(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("ProfileScheduler stopped.")

    def run_profile_sync(self):
        logger.info("--- AI FINANCIAL PROFILE GENERATION STARTED ---")
        db_session = Session(engine)
        try:
            profile = self.service.generate_financial_profile(db_session)
            if profile:
                logger.info(f"Generated new Financial Profile (Version {profile.profile_version}).")
            else:
                logger.info("Financial Profile generation skipped or failed.")
        except Exception as e:
            logger.error(f"Error during AI Financial Profile Generation: {str(e)}", exc_info=True)
        finally:
            db_session.close()
            logger.info("--- AI FINANCIAL PROFILE GENERATION ENDED ---")
