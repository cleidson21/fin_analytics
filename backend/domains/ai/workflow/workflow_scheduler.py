import logging
from apscheduler.schedulers.background import BackgroundScheduler
from backend.domains.ai.workflow.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

class WorkflowScheduler:
    def __init__(self, service: WorkflowService):
        self.service = service
        self._scheduler = BackgroundScheduler()

    def start(self):
        logger.info("Starting WorkflowScheduler...")
        
        # Daily Workflow at 02:00 AM (Replacing old MarketData + Insights + Executive)
        self._scheduler.add_job(
            self.run_daily_job,
            'cron',
            hour=2, 
            minute=0,
            id='workflow_daily'
        )

        # Weekly Workflow every Sunday at 04:00 AM (Replacing old Profile + Coach)
        self._scheduler.add_job(
            self.run_weekly_job,
            'cron',
            day_of_week='sun',
            hour=4,
            minute=0,
            id='workflow_weekly'
        )

        # Monthly Workflow on the 1st day at 06:00 AM (Replacing old Memory + Personalization)
        self._scheduler.add_job(
            self.run_monthly_job,
            'cron',
            day=1,
            hour=6,
            minute=0,
            id='workflow_monthly'
        )

        self._scheduler.start()

    def stop(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("WorkflowScheduler stopped.")

    def run_daily_job(self):
        self.service.run_daily(trigger="scheduler")

    def run_weekly_job(self):
        self.service.run_weekly(trigger="scheduler")

    def run_monthly_job(self):
        self.service.run_monthly(trigger="scheduler")
