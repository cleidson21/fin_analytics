import logging
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from backend.shared.db import engine
from backend.domains.ai.insights.insight_service import AIInsightService

logger = logging.getLogger(__name__)

class InsightScheduler:
    def __init__(self, service: AIInsightService):
        self.service = service
        self._scheduler = BackgroundScheduler()

    def start(self):
        logger.info("Starting InsightScheduler (Daily)...")
        # Runs once a day, conceptually after market data. We can schedule it at 02:00 AM or just interval=1 day
        self._scheduler.add_job(
            self.run_insights_sync,
            'cron',
            hour=2, # Run at 2 AM
            minute=0,
            id='proactive_insights_sync'
        )
        self._scheduler.start()
        
        # Also run at startup to guarantee insights are available
        self._scheduler.add_job(self.run_insights_sync, 'date', id='startup_insights_sync')

    def stop(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("InsightScheduler stopped.")

    def run_insights_sync(self):
        logger.info("--- AI INSIGHTS GENERATION STARTED ---")
        db_session = Session(engine)
        try:
            insights = self.service.generate_proactive_insights(db_session)
            if insights:
                logger.info(f"Generated {len(insights)} new proactive insights.")
            else:
                logger.info("No new insights generated (cached or insufficient data).")
        except Exception as e:
            logger.error(f"Error during AI Insights Generation: {str(e)}", exc_info=True)
        finally:
            db_session.close()
            logger.info("--- AI INSIGHTS GENERATION ENDED ---")
