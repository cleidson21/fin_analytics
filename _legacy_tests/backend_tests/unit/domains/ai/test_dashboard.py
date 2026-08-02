import unittest
from unittest.mock import MagicMock
from backend.domains.ai.dashboard.dashboard_service import DashboardDeliveryService

class TestDashboardDelivery(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.service = DashboardDeliveryService(self.mock_repo)
        self.session = MagicMock()

    def test_get_dashboard_view_model_empty(self):
        self.mock_repo.get_orchestrator_context.return_value = {
            "status": "degraded",
            "cache_key": "empty_hash",
            "context": {
                "profile": {},
                "coach": {},
                "executive": {},
                "personalization": {},
                "memory": {},
                "insights": {},
                "planning": {}
            }
        }
        
        vm = self.service.get_dashboard_view_model(self.session)
        self.assertEqual(vm.status, "degraded")
        self.assertEqual(vm.cache_key, "empty_hash")
        self.assertEqual(vm.profile["investor_profile"], "Desconhecido")
        self.assertEqual(vm.coach["weekly_focus"], "N/A")
        self.assertEqual(len(vm.insights), 0)
        self.assertEqual(len(vm.priorities), 0)

    def test_get_dashboard_view_model_complete(self):
        self.mock_repo.get_orchestrator_context.return_value = {
            "status": "healthy",
            "cache_key": "full_hash",
            "context": {
                "profile": {"investor_profile": "Aggressive", "investment_style": "Growth"},
                "coach": {"weekly_focus": "Save money", "monthly_focus": "Invest", "priority_actions": '["Action 1", "Action 2"]'},
                "executive": {"summary": "Great summary", "recommended_focus": "Tech"},
                "personalization": {"theme": "dark"},
                "memory": {},
                "insights": {"active_insights": [{"title": "Insight 1", "severity": "High"}]},
                "planning": {"simulations": []}
            }
        }
        
        vm = self.service.get_dashboard_view_model(self.session)
        self.assertEqual(vm.status, "healthy")
        self.assertEqual(vm.summary["text"], "Great summary")
        self.assertEqual(vm.profile["investor_profile"], "Aggressive")
        self.assertEqual(len(vm.insights), 1)
        self.assertEqual(len(vm.priorities), 2)
        
        # Test Cache Hit
        self.mock_repo.get_orchestrator_context.return_value = {
            "status": "healthy",
            "cache_key": "full_hash",
            "context": {}
        }
        vm2 = self.service.get_dashboard_view_model(self.session)
        self.assertEqual(vm2.summary["text"], "Great summary") # It should be served from memory

if __name__ == '__main__':
    unittest.main()
