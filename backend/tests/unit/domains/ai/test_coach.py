import unittest
from unittest.mock import MagicMock
from backend.domains.ai.coach.coach_service import AICoachService
from backend.domains.ai.coach.coach_scheduler import CoachScheduler
from backend.domains.ai.coach.coach_models import CoachRecord
from backend.domains.ai.schemas import AIResponseDTO

class TestAICoach(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_repo = MagicMock()
        self.service = AICoachService(self.mock_provider, self.mock_repo)
        self.session = MagicMock()

    def test_generate_coach_no_profile(self):
        self.mock_repo.get_latest_coach_plan.return_value = None
        self.mock_repo.get_context.return_value = {
            "profile": {},
            "executive": {},
            "planning": [],
            "insights": [],
            "macro": {},
            "cache_key": "empty_cache_key"
        }
        
        mock_response = AIResponseDTO(
            success=True,
            data={
                "action_plan": "Crie seu perfil.",
                "weekly_focus": "Aportar",
                "monthly_focus": "Organizar",
                "priority_actions": ["Criar meta"],
                "recommended_habits": ["Acompanhar", "Estudar"],
                "portfolio_observations": "Vazio",
                "risk_observations": "N/A",
                "planning_observations": "N/A"
            },
            model="gemini",
            tokens=150,
            latency=1.5
        )
        self.mock_provider.generate_json.return_value = mock_response
        
        record = self.service.generate_coach_plan(self.session)
        self.assertIsNotNone(record)
        self.assertEqual(record.coach_version, 1)
        self.assertEqual(record.weekly_focus, "Aportar")
        self.mock_repo.save_coach_plan.assert_called_once()

    def test_generate_coach_cache_hit(self):
        self.mock_repo.get_context.return_value = {"cache_key": "hit_key"}
        mock_latest = CoachRecord(
            id="1", coach_version=2, action_plan="Plano", weekly_focus="Foco W",
            monthly_focus="Foco M", recommended_habits="[]", priority_actions="[]",
            portfolio_observations="Obs P", risk_observations="Obs R",
            planning_observations="Obs PL", generated_at="2026-07-16T10:00:00Z",
            expires_at=None, cache_key="hit_key"
        )
        self.mock_repo.get_latest_coach_plan.return_value = mock_latest
        
        record = self.service.generate_coach_plan(self.session)
        self.assertEqual(record.coach_version, 2)
        self.mock_provider.generate_json.assert_not_called()

    def test_get_financial_coach(self):
        mock_latest = CoachRecord(
            id="1", coach_version=1, action_plan="Plano", weekly_focus="Foco W",
            monthly_focus="Foco M", recommended_habits='["Hab 1", "Hab 2"]', priority_actions='["Ação 1"]',
            portfolio_observations="Obs P", risk_observations="Obs R",
            planning_observations="Obs PL", generated_at="2026-07-16T10:00:00Z",
            expires_at=None, cache_key="hit_key"
        )
        self.mock_repo.get_latest_coach_plan.return_value = mock_latest
        
        dto = self.service.get_financial_coach_plan(self.session)
        self.assertEqual(dto.weekly_focus, "Foco W")
        self.assertEqual(len(dto.recommended_habits), 2)
        self.assertEqual(dto.priority_actions[0], "Ação 1")

    def test_scheduler_lifecycle(self):
        scheduler = CoachScheduler(self.service)
        scheduler._scheduler = MagicMock()
        
        scheduler.start()
        self.assertEqual(scheduler._scheduler.add_job.call_count, 2)
        
        scheduler._scheduler.running = True
        scheduler.stop()
        scheduler._scheduler.shutdown.assert_called_once()

if __name__ == '__main__':
    unittest.main()
