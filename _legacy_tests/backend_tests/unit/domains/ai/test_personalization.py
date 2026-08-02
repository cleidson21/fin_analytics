import unittest
from unittest.mock import MagicMock
from backend.domains.ai.personalization.personalization_service import AIPersonalizationService
from backend.domains.ai.personalization.personalization_scheduler import PersonalizationScheduler
from backend.domains.ai.personalization.personalization_models import PersonalizationRecord
from backend.domains.ai.schemas import AIResponseDTO

class TestAIPersonalization(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_repo = MagicMock()
        self.service = AIPersonalizationService(self.mock_provider, self.mock_repo)
        self.session = MagicMock()

    def test_generate_personalization_empty(self):
        self.mock_repo.get_latest_personalization.return_value = None
        self.mock_repo.get_context.return_value = {
            "memory": {},
            "profile": {},
            "coach": {},
            "executive": {},
            "insights": [],
            "cache_key": "empty_cache_key"
        }
        
        mock_response = AIResponseDTO(
            success=True,
            data={
                "communication_style": "padrão",
                "detail_level": "médio",
                "priority_topics": ["patrimônio"],
                "dashboard_focus": ["evolução patrimonial"],
                "preferred_frequency": "semanal",
                "notification_preferences": [],
                "learning_preferences": [],
                "language_profile": "simples",
                "summary_preferences": "texto"
            },
            model="gemini",
            tokens=150,
            latency=1.5
        )
        self.mock_provider.generate_json.return_value = mock_response
        
        record = self.service.generate_personalization(self.session)
        self.assertIsNotNone(record)
        self.assertEqual(record.personalization_version, 1)
        self.assertEqual(record.communication_style, "padrão")
        self.mock_repo.save_personalization.assert_called_once()

    def test_generate_personalization_cache_hit(self):
        self.mock_repo.get_context.return_value = {"cache_key": "hit_key"}
        mock_latest = PersonalizationRecord(
            id="1", personalization_version=2, communication_style="executivo", detail_level="alto",
            priority_topics="[]", preferred_frequency="diária", dashboard_focus="[]",
            notification_preferences="[]", learning_preferences="[]", language_profile="corp",
            summary_preferences="visual", generated_at="2026-07-16T10:00:00Z",
            expires_at=None, cache_key="hit_key"
        )
        self.mock_repo.get_latest_personalization.return_value = mock_latest
        
        record = self.service.generate_personalization(self.session)
        self.assertEqual(record.personalization_version, 2)
        self.mock_provider.generate_json.assert_not_called()

    def test_get_personalization(self):
        mock_latest = PersonalizationRecord(
            id="1", personalization_version=1, communication_style="técnico", detail_level="alto",
            priority_topics='["risco", "alocação"]', preferred_frequency="mensal", dashboard_focus='["risco"]',
            notification_preferences="[]", learning_preferences="[]", language_profile="técnica",
            summary_preferences="gráficos", generated_at="2026-07-16T10:00:00Z",
            expires_at=None, cache_key="hit_key"
        )
        self.mock_repo.get_latest_personalization.return_value = mock_latest
        
        dto = self.service.get_personalization(self.session)
        self.assertEqual(dto.communication_style, "técnico")
        self.assertEqual(len(dto.priority_topics), 2)
        self.assertEqual(dto.priority_topics[0], "risco")

    def test_scheduler_lifecycle(self):
        scheduler = PersonalizationScheduler(self.service)
        scheduler._scheduler = MagicMock()
        
        scheduler.start()
        self.assertEqual(scheduler._scheduler.add_job.call_count, 2)
        
        scheduler._scheduler.running = True
        scheduler.stop()
        scheduler._scheduler.shutdown.assert_called_once()

if __name__ == '__main__':
    unittest.main()
