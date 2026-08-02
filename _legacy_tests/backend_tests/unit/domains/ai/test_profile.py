import unittest
from unittest.mock import MagicMock
from backend.domains.ai.profile.profile_service import AIProfileService
from backend.domains.ai.profile.profile_scheduler import ProfileScheduler
from backend.domains.ai.profile.profile_models import ProfileRecord
from backend.domains.ai.schemas import AIResponseDTO

class TestAIProfile(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_repo = MagicMock()
        self.service = AIProfileService(self.mock_provider, self.mock_repo)
        self.session = MagicMock()

    def test_generate_profile_empty(self):
        self.mock_repo.get_latest_profile.return_value = None
        self.mock_repo.get_context.return_value = {
            "portfolio": [],
            "briefs": [],
            "planning": [],
            "insights": [],
            "macro": {},
            "cache_key": "empty_cache_key"
        }
        
        mock_response = AIResponseDTO(
            success=True,
            data={
                "investor_profile": "Desconhecido",
                "risk_tolerance": "N/A",
                "investment_style": "N/A",
                "portfolio_maturity": "N/A",
                "diversification_score": "N/A",
                "cash_behavior": "N/A",
                "dividend_focus": "N/A",
                "consistency_score": "N/A",
                "planning_score": "N/A",
                "macro_sensitivity": "N/A",
                "behavior_summary": "Faltam dados.",
                "strengths": [],
                "attention_points": ["Inicie seus aportes."]
            },
            model="gemini",
            tokens=150,
            latency=1.5
        )
        self.mock_provider.generate_json.return_value = mock_response
        
        record = self.service.generate_financial_profile(self.session)
        self.assertIsNotNone(record)
        self.assertEqual(record.profile_version, 1)
        self.assertEqual(record.investor_profile, "Desconhecido")
        self.mock_repo.save_profile.assert_called_once()

    def test_generate_profile_cache_hit(self):
        self.mock_repo.get_context.return_value = {"cache_key": "hit_key"}
        mock_latest = ProfileRecord(
            id="1", profile_version=2, investor_profile="Moderado", risk_tolerance="Media",
            investment_style="Dividendos", portfolio_maturity="Acumulação", diversification_score="Alta",
            cash_behavior="N/A", dividend_focus="N/A", consistency_score="N/A",
            planning_score="N/A", macro_sensitivity="N/A", behavior_summary="N/A",
            strengths="[]", attention_points="[]", generated_at="2026-07-16T10:00:00Z",
            expires_at=None, cache_key="hit_key"
        )
        self.mock_repo.get_latest_profile.return_value = mock_latest
        
        record = self.service.generate_financial_profile(self.session)
        self.assertEqual(record.profile_version, 2)
        self.mock_provider.generate_json.assert_not_called()

    def test_get_financial_profile(self):
        mock_latest = ProfileRecord(
            id="1", profile_version=1, investor_profile="Conservador", risk_tolerance="Baixa",
            investment_style="Renda Fixa", portfolio_maturity="Acumulação", diversification_score="Media",
            cash_behavior="N/A", dividend_focus="N/A", consistency_score="N/A",
            planning_score="N/A", macro_sensitivity="N/A", behavior_summary="N/A",
            strengths='["Disciplina"]', attention_points='["Inflacao"]', generated_at="2026-07-16T10:00:00Z",
            expires_at=None, cache_key="hit_key"
        )
        self.mock_repo.get_latest_profile.return_value = mock_latest
        
        dto = self.service.get_financial_profile(self.session)
        self.assertEqual(dto.profile, "Conservador")
        self.assertEqual(len(dto.strengths), 1)
        self.assertEqual(dto.strengths[0], "Disciplina")

    def test_scheduler_lifecycle(self):
        scheduler = ProfileScheduler(self.service)
        scheduler._scheduler = MagicMock()
        
        scheduler.start()
        self.assertEqual(scheduler._scheduler.add_job.call_count, 2)
        
        scheduler._scheduler.running = True
        scheduler.stop()
        scheduler._scheduler.shutdown.assert_called_once()

if __name__ == '__main__':
    unittest.main()
