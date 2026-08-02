import unittest
from unittest.mock import MagicMock
from backend.domains.ai.memory.memory_service import AIMemoryService
from backend.domains.ai.memory.memory_scheduler import MemoryScheduler
from backend.domains.ai.memory.memory_models import MemoryRecord
from backend.domains.ai.schemas import AIResponseDTO

class TestAIMemory(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_repo = MagicMock()
        self.service = AIMemoryService(self.mock_provider, self.mock_repo)
        self.session = MagicMock()

    def test_generate_memory_empty(self):
        self.mock_repo.get_latest_memory.return_value = None
        self.mock_repo.get_context.return_value = {
            "portfolio_summary": {"first_snapshot": "N/A", "last_snapshot": "N/A"},
            "profile_history": [],
            "coach_history": [],
            "executive_history": [],
            "planning_history": [],
            "cache_key": "empty_cache_key"
        }
        
        mock_response = AIResponseDTO(
            success=True,
            data={
                "investment_preferences": ["Nenhuma detectada"],
                "behavior_patterns": ["Sem histórico"],
                "historical_strengths": ["Potencial de início"],
                "historical_attention_points": ["Sem consistência ainda"],
                "recurring_goals": [],
                "learning_summary": "Usuário recém chegado ao sistema.",
                "confidence_score": 0.1
            },
            model="gemini",
            tokens=150,
            latency=1.5
        )
        self.mock_provider.generate_json.return_value = mock_response
        
        record = self.service.generate_memory(self.session)
        self.assertIsNotNone(record)
        self.assertEqual(record.memory_version, 1)
        self.assertEqual(record.confidence_score, 0.1)
        self.mock_repo.save_memory.assert_called_once()

    def test_generate_memory_cache_hit(self):
        self.mock_repo.get_context.return_value = {"cache_key": "hit_key"}
        mock_latest = MemoryRecord(
            id="1", memory_version=2, investment_preferences="[]", behavior_patterns="[]",
            historical_strengths="[]", historical_attention_points="[]", recurring_goals="[]",
            learning_summary="Sumario", confidence_score=0.9, generated_at="2026-07-16T10:00:00Z",
            expires_at=None, cache_key="hit_key"
        )
        self.mock_repo.get_latest_memory.return_value = mock_latest
        
        record = self.service.generate_memory(self.session)
        self.assertEqual(record.memory_version, 2)
        self.mock_provider.generate_json.assert_not_called()

    def test_get_financial_memory(self):
        mock_latest = MemoryRecord(
            id="1", memory_version=1, investment_preferences='["Foco em Renda"]', behavior_patterns='["Constante"]',
            historical_strengths="[]", historical_attention_points="[]", recurring_goals='["Aposentadoria"]',
            learning_summary="Aprende rápido", confidence_score=0.95, generated_at="2026-07-16T10:00:00Z",
            expires_at=None, cache_key="hit_key"
        )
        self.mock_repo.get_latest_memory.return_value = mock_latest
        
        dto = self.service.get_financial_memory(self.session)
        self.assertEqual(len(dto.investment_preferences), 1)
        self.assertEqual(dto.investment_preferences[0], "Foco em Renda")
        self.assertEqual(dto.confidence_score, 0.95)

    def test_scheduler_lifecycle(self):
        scheduler = MemoryScheduler(self.service)
        scheduler._scheduler = MagicMock()
        
        scheduler.start()
        self.assertEqual(scheduler._scheduler.add_job.call_count, 2)
        
        scheduler._scheduler.running = True
        scheduler.stop()
        scheduler._scheduler.shutdown.assert_called_once()

if __name__ == '__main__':
    unittest.main()
