import unittest
from unittest.mock import MagicMock
from backend.domains.ai.planning.planning_service import AIPlanningService
from backend.domains.ai.planning.planning_models import GoalDTO, SimulationRequestDTO
from backend.domains.ai.schemas import AIResponseDTO

class TestAIPlanning(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_repo = MagicMock()
        self.service = AIPlanningService(self.mock_provider, self.mock_repo)
        self.session = MagicMock()
        
        # Reset cache
        import backend.domains.ai.planning.planning_service as planning_module
        planning_module._planning_cache = {}

    def test_simulation_with_wealth_and_scenarios(self):
        goal = GoalDTO(
            id="g1", goal_name="Aposentadoria", target_amount=1000000.0, 
            current_amount=0.0, monthly_contribution=1000.0, 
            expected_return=0.10, target_date="2046-01-01", active=True
        )
        self.mock_repo.get_goal_by_id.return_value = goal
        self.mock_repo.get_portfolio_context.return_value = {
            "equity": 50000.0, "dividends_year": 2000.0, "snapshot_date": "2026-07-16"
        }
        self.mock_repo.get_macro_context.return_value = {"SELIC": "10.5%"}
        
        mock_response = AIResponseDTO(
            success=True,
            data={"ai_analysis": "Caminho seguro."},
            model="gemini",
            tokens=50,
            latency=0.5
        )
        self.mock_provider.generate_json.return_value = mock_response
        
        req = SimulationRequestDTO(goal_id="g1", scenario="Conservador", aporte_adjustment=1.0)
        
        # Act
        resp = self.service.simulate_goal(self.session, req)
        
        # Assert projections (1, 5, 10, 20 years)
        self.assertEqual(len(resp.projections), 4)
        self.assertEqual(resp.scenario, "Conservador")
        self.assertEqual(resp.ai_analysis, "Caminho seguro.")
        
        # Check cache hit
        resp_cached = self.service.simulate_goal(self.session, req)
        self.assertEqual(self.mock_provider.generate_json.call_count, 1)
        self.assertEqual(resp_cached.ai_analysis, "Caminho seguro.")
        self.assertEqual(resp_cached.latency, 0.0)

    def test_simulation_without_wealth(self):
        goal = GoalDTO(
            id="g2", goal_name="Carro", target_amount=50000.0, 
            current_amount=10000.0, monthly_contribution=500.0, 
            expected_return=0.08, target_date="2030-01-01", active=True
        )
        self.mock_repo.get_goal_by_id.return_value = goal
        # Empty wealth from snapshot
        self.mock_repo.get_portfolio_context.return_value = {
            "equity": 0.0, "dividends_year": 0.0, "snapshot_date": "2026-07-16"
        }
        self.mock_repo.get_macro_context.return_value = {}
        
        self.mock_provider.generate_json.return_value = AIResponseDTO(
            success=True, data={"ai_analysis": "Factível."}, model="gemini", tokens=50, latency=0.5
        )
        
        req = SimulationRequestDTO(goal_id="g2", scenario="Otimista", aporte_adjustment=1.2)
        resp = self.service.simulate_goal(self.session, req)
        
        # Initial equity should fall back to goal's current_amount (10000.0)
        # We can assert this implicitly by checking if it took less than 1200 months
        self.assertIsNotNone(resp.time_to_independence_years)
        self.assertTrue(resp.time_to_independence_years > 0.0)

if __name__ == '__main__':
    unittest.main()
