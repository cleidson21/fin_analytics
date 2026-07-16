import unittest
from unittest.mock import MagicMock
from backend.domains.ai.executive.executive_service import AIExecutiveService
from backend.domains.ai.executive.executive_scheduler import ExecutiveScheduler
from backend.domains.ai.executive.executive_models import ExecutiveBriefRecord
from backend.domains.ai.schemas import AIResponseDTO

class TestAIExecutive(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_repo = MagicMock()
        self.service = AIExecutiveService(self.mock_provider, self.mock_repo)
        self.session = MagicMock()

    def test_generate_brief_empty_wealth(self):
        self.mock_repo.get_latest_brief.return_value = None
        self.mock_repo.get_context.return_value = {
            "portfolio": {"snapshot_date": "1970-01-01", "equity": 0.0, "dividends_total": 0.0, "dividends_year": 0.0, "allocation": {}},
            "macro": {},
            "macro_date": "1970-01-01",
            "insights": [],
            "planning": [],
            "cache_key": "1970-01-01|1970-01-01|hash1|hash2"
        }
        
        mock_response = AIResponseDTO(
            success=True,
            data={
                "summary": "Nenhum dado.",
                "portfolio_summary": "Vazio",
                "market_summary": "Vazio",
                "insights_summary": "Vazio",
                "planning_summary": "Vazio",
                "risk_summary": "Vazio",
                "recommended_focus": "Aportar"
            },
            model="gemini",
            tokens=50,
            latency=0.5
        )
        self.mock_provider.generate_json.return_value = mock_response
        
        record = self.service.generate_executive_brief(self.session)
        self.assertIsNotNone(record)
        self.assertEqual(record.summary, "Nenhum dado.")
        self.assertEqual(record.recommended_focus, "Aportar")
        self.mock_repo.save_brief.assert_called_once()

    def test_generate_brief_cache_hit(self):
        self.mock_repo.get_context.return_value = {"cache_key": "hit_key"}
        mock_latest = ExecutiveBriefRecord(
            id="1", brief_date="2026-07-16", summary="hit", portfolio_summary="",
            market_summary="", insights_summary="", planning_summary="",
            risk_summary="", recommended_focus="", generated_at="2026-07-16T10:00:00Z",
            expires_at=None, cache_key="hit_key"
        )
        self.mock_repo.get_latest_brief.return_value = mock_latest
        
        record = self.service.generate_executive_brief(self.session)
        self.assertEqual(record.summary, "hit")
        self.mock_provider.generate_json.assert_not_called()

    def test_get_executive_brief(self):
        mock_latest = ExecutiveBriefRecord(
            id="1", brief_date="2026-07-16", summary="Resumo", portfolio_summary="Port",
            market_summary="Mark", insights_summary="Ins", planning_summary="Plan",
            risk_summary="Risk", recommended_focus="A, B, C", generated_at="2026-07-16T10:00:00Z",
            expires_at=None, cache_key="key1"
        )
        self.mock_repo.get_latest_brief.return_value = mock_latest
        
        dto = self.service.get_executive_brief(self.session)
        self.assertEqual(dto.summary, "Resumo")
        self.assertEqual(len(dto.priorities), 3)
        self.assertEqual(dto.priorities[0], "A")

    def test_scheduler_lifecycle(self):
        scheduler = ExecutiveScheduler(self.service)
        scheduler._scheduler = MagicMock()
        
        scheduler.start()
        self.assertEqual(scheduler._scheduler.add_job.call_count, 2)
        
        scheduler._scheduler.running = True
        scheduler.stop()
        scheduler._scheduler.shutdown.assert_called_once()

if __name__ == '__main__':
    unittest.main()
