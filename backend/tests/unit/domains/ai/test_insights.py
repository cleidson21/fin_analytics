import unittest
from unittest.mock import MagicMock
from backend.domains.ai.insights.insight_service import AIInsightService
from backend.domains.ai.insights.insight_scheduler import InsightScheduler
from backend.domains.ai.schemas import AIResponseDTO

class TestAIInsights(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_repo = MagicMock()
        self.service = AIInsightService(self.mock_provider, self.mock_repo)
        self.session = MagicMock()
        
    def test_generate_proactive_insights_cache_hit(self):
        self.mock_repo.get_latest_context_dates.return_value = {"snapshot_date": "2026-07-16", "macro_date": "2026-07-16"}
        self.mock_repo.has_insights_for_cache.return_value = True
        
        insights = self.service.generate_proactive_insights(self.session)
        self.assertEqual(len(insights), 0)
        self.mock_provider.generate_json.assert_not_called()

    def test_generate_proactive_insights_success(self):
        self.mock_repo.get_latest_context_dates.return_value = {"snapshot_date": "2026-07-16", "macro_date": "2026-07-16"}
        self.mock_repo.has_insights_for_cache.return_value = False
        self.mock_repo.get_portfolio_summary.return_value = [{"date": "2026-07-16", "equity": 1000, "dividends": 10}]
        self.mock_repo.get_allocation_summary.return_value = {"Ações": 50.0, "FIIs": 50.0}
        self.mock_repo.get_macro_summary.return_value = {"SELIC": "10.5%"}
        
        mock_response = AIResponseDTO(
            success=True,
            data={"insights": [
                {
                    "insight_type": "Patrimônio",
                    "severity": "success",
                    "title": "Crescimento Consistente",
                    "description": "Seu patrimônio cresceu.",
                    "recommendation": "Mantenha os aportes."
                }
            ]},
            model="gemini",
            tokens=100,
            latency=1.0
        )
        self.mock_provider.generate_json.return_value = mock_response
        
        insights = self.service.generate_proactive_insights(self.session)
        self.assertEqual(len(insights), 1)
        self.assertEqual(insights[0].insight_type, "Patrimônio")
        self.assertEqual(insights[0].severity, "success")
        self.mock_repo.save_insights.assert_called_once()
        
    def test_scheduler_lifecycle(self):
        scheduler = InsightScheduler(self.service)
        scheduler._scheduler = MagicMock()
        
        scheduler.start()
        self.assertEqual(scheduler._scheduler.add_job.call_count, 2)
        scheduler._scheduler.start.assert_called_once()
        
        scheduler._scheduler.running = True
        scheduler.stop()
        scheduler._scheduler.shutdown.assert_called_once()

if __name__ == '__main__':
    unittest.main()
