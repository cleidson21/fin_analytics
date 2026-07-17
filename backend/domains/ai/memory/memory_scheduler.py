import logging
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from backend.shared.db import engine
from backend.domains.ai.memory.memory_service import AIMemoryService

logger = logging.getLogger(__name__)

class MemoryScheduler:
    def __init__(self, service: AIMemoryService):
        self.service = service
        self._scheduler = BackgroundScheduler()

    def start(self):
        logger.info("Starting MemoryScheduler (Monthly)...")
        # Run monthly on the 1st day at 06:00 AM
        self._scheduler.add_job(
            self.run_memory_sync,
            'cron',
            day=1,
            hour=6, 
            minute=0,
            id='financial_memory_sync'
        )
        self._scheduler.start()
        
        # Ensure it runs at least once on startup if not present
        self._scheduler.add_job(self.run_memory_sync, 'date', id='startup_memory_sync')

    def stop(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("MemoryScheduler stopped.")

    def run_memory_sync(self):
        logger.info("--- AI FINANCIAL MEMORY GENERATION STARTED ---")
        db_session = Session(engine)
        try:
            memory = self.service.generate_memory(db_session)
            if memory:
                logger.info(f"Generated new Financial Memory (Version {memory.memory_version}).")
            else:
                logger.info("Financial Memory generation skipped or failed.")
        except Exception as e:
            logger.error(f"Error during AI Financial Memory Generation: {str(e)}", exc_info=True)
        finally:
            db_session.close()
            logger.info("--- AI FINANCIAL MEMORY GENERATION ENDED ---")
