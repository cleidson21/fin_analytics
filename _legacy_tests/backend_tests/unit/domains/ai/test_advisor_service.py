import unittest
from unittest.mock import MagicMock
from backend.domains.ai.advisor.advisor_service import AIAdvisorService
from backend.domains.ai.advisor.advisor_models import AdvisorRequestDTO
from backend.domains.ai.exceptions import AITimeoutException
from backend.domains.ai.schemas import AIResponseDTO

class TestAdvisorService(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_repo = MagicMock()
        self.service = AIAdvisorService(self.mock_provider, self.mock_repo)
        self.session = MagicMock()
        
        # Reset cache for testing isolation
        import backend.domains.ai.advisor.advisor_service as advisor_module
        advisor_module._advisor_cache = {}

    def test_build_context_with_wealth(self):
        self.mock_repo.get_latest_portfolio_snapshot.return_value = {
            "patrimonio_atual": 150000.0,
            "patrimonio_investido": 120000.0,
            "patrimonio_liquido": 30000.0,
            "dividendos_acumulados": 5000.0,
            "rentabilidade_historica": 25.0,
            "sharpe": 1.2,
            "beta": 0.9,
            "volatilidade": 0.15
        }
        self.mock_repo.get_top_positions.return_value = {
            "maior_posicao": "WEGE3",
            "menor_posicao": "OIBR3",
            "top_5": []
        }
        self.mock_repo.get_latest_macro.return_value = {"SELIC": "10.5%"}
        
        context = self.service.build_context(self.session)
        self.assertEqual(context.patrimonio_atual, 150000.0)
        self.assertEqual(context.maior_posicao, "WEGE3")
        self.assertEqual(context.indicadores_macro["SELIC"], "10.5%")

    def test_build_context_without_wealth(self):
        self.mock_repo.get_latest_portfolio_snapshot.return_value = {
            "patrimonio_atual": 0.0,
            "patrimonio_investido": 0.0,
            "patrimonio_liquido": 0.0,
            "dividendos_acumulados": 0.0,
            "rentabilidade_historica": 0.0,
            "sharpe": 0.0,
            "beta": 0.0,
            "volatilidade": 0.0
        }
        self.mock_repo.get_top_positions.return_value = {
            "maior_posicao": None,
            "menor_posicao": None,
            "top_5": []
        }
        self.mock_repo.get_latest_macro.return_value = {}
        
        context = self.service.build_context(self.session)
        self.assertEqual(context.patrimonio_atual, 0.0)
        self.assertIsNone(context.maior_posicao)

    def test_answer_question_cache_hit(self):
        # Setup context
        self.test_build_context_with_wealth()
        
        # Setup mock provider response
        mock_response = AIResponseDTO(
            success=True,
            data={"answer": "Sua carteira está excelente."},
            model="gemini",
            tokens=100,
            latency=1.5
        )
        self.mock_provider.generate_json.return_value = mock_response
        
        req = AdvisorRequestDTO(question="Como está minha carteira?")
        
        # First call (miss)
        resp1 = self.service.answer_question(self.session, req)
        self.assertEqual(self.mock_provider.generate_json.call_count, 1)
        self.assertEqual(resp1.answer, "Sua carteira está excelente.")
        
        # Second call (hit)
        resp2 = self.service.answer_question(self.session, req)
        self.assertEqual(self.mock_provider.generate_json.call_count, 1) # API NOT CALLED AGAIN
        self.assertEqual(resp2.answer, "Sua carteira está excelente.")
        self.assertEqual(resp2.latency, 0.0)

    def test_timeout_exception(self):
        self.test_build_context_with_wealth()
        
        self.mock_provider.generate_json.side_effect = AITimeoutException("Timeout")
        req = AdvisorRequestDTO(question="Timeout test?")
        
        with self.assertRaises(AITimeoutException):
            self.service.answer_question(self.session, req)

if __name__ == '__main__':
    unittest.main()
