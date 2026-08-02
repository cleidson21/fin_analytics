import unittest
from unittest.mock import MagicMock
from backend.domains.ai.orchestrator.orchestrator_service import AIOrchestratorService

class TestAIOrchestrator(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.service = AIOrchestratorService(self.mock_repo)
        self.session = MagicMock()

    def test_get_orchestrator_status_all_ok(self):
        self.mock_repo.get_unified_context.return_value = {
            "insights": {"data": "ok"},
            "planning": {"data": "ok"},
            "executive": {"data": "ok"},
            "profile": {"data": "ok"},
            "coach": {"data": "ok"},
            "memory": {"data": "ok"},
            "personalization": {"data": "ok"}
        }
        
        status = self.service.get_orchestrator_status(self.session)
        self.assertEqual(status.status, "healthy")
        self.assertEqual(status.modules["insights"], "ok")
        self.assertEqual(status.modules["personalization"], "ok")

    def test_get_orchestrator_status_degraded(self):
        self.mock_repo.get_unified_context.return_value = {
            "insights": {"data": "ok"},
            "planning": None,
            "executive": {"data": "ok"},
            "profile": None,
            "coach": {"data": "ok"},
            "memory": {"data": "ok"},
            "personalization": None
        }
        
        status = self.service.get_orchestrator_status(self.session)
        self.assertEqual(status.status, "degraded")
        self.assertEqual(status.modules["planning"], "missing")
        self.assertEqual(status.modules["profile"], "missing")
        self.assertEqual(status.modules["personalization"], "missing")
        self.assertEqual(status.modules["advisor"], "ok")

    def test_get_unified_context(self):
        self.mock_repo.get_unified_context.return_value = {
            "profile": {"style": "Aggressive"},
            "cache_key": "test_cache"
        }
        
        context = self.service.get_unified_context(self.session)
        self.assertEqual(context.cache_key, "test_cache")
        self.assertEqual(context.profile["style"], "Aggressive")
        self.assertIsNone(context.coach)

if __name__ == '__main__':
    unittest.main()
