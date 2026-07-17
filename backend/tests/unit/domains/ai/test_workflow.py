import unittest
from unittest.mock import MagicMock, patch
from backend.domains.ai.workflow.workflow_service import WorkflowService
from backend.domains.ai.workflow.workflow_repository import WorkflowRepository

class TestWorkflowEngine(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.service = WorkflowService(self.mock_repo)

    @patch('backend.domains.market_data.service.MarketDataService.update_market_data')
    @patch('backend.domains.market_data.macro_service.MacroIndicatorsService.update_indicators')
    @patch('backend.domains.ai.workflow.workflow_service.AIInsightService.generate_proactive_insights')
    @patch('backend.domains.ai.workflow.workflow_service.AIExecutiveService.generate_executive_brief')
    @patch('backend.domains.ai.workflow.workflow_service.AIOrchestratorService.get_unified_context')
    def test_run_daily_workflow(self, mock_orch, mock_exec, mock_ins, mock_macro, mock_mkt):
        self.service.run_daily(trigger="test")
        mock_mkt.assert_called_once()
        mock_macro.assert_called_once()
        mock_ins.assert_called_once()
        mock_exec.assert_called_once()
        mock_orch.assert_called_once()
        self.mock_repo.create_run.assert_called_once()
        # Should be updated after each step + 1 for start, 1 for final
        self.assertTrue(self.mock_repo.update_run.call_count > 1)

    @patch('backend.domains.ai.workflow.workflow_service.AIProfileService.generate_financial_profile')
    @patch('backend.domains.ai.workflow.workflow_service.AICoachService.generate_coach_plan')
    def test_run_weekly_workflow(self, mock_coach, mock_profile):
        self.service.run_weekly(trigger="manual")
        mock_profile.assert_called_once()
        mock_coach.assert_called_once()
        self.mock_repo.create_run.assert_called_once()
        
    @patch('backend.domains.ai.workflow.workflow_service.AIMemoryService.generate_memory')
    @patch('backend.domains.ai.workflow.workflow_service.AIPersonalizationService.generate_personalization')
    def test_run_monthly_workflow(self, mock_pers, mock_mem):
        self.service.run_monthly(trigger="manual")
        mock_mem.assert_called_once()
        mock_pers.assert_called_once()

    @patch('backend.domains.market_data.service.MarketDataService.update_market_data')
    def test_workflow_failure_intermediate_step(self, mock_mkt):
        mock_mkt.side_effect = Exception("Failed Market Data")
        self.service.run_daily(trigger="test")
        
        args, kwargs = self.mock_repo.update_run.call_args_list[-1]
        record = args[1]
        self.assertEqual(record.status, "FAILED")
        self.assertEqual(record.failed_step, "Market Data")
        self.assertEqual(record.error_message, "Failed Market Data")
        
    def test_get_status(self):
        self.mock_repo.get_last_run_status.side_effect = ["SUCCESS", "FAILED", "PENDING"]
        self.mock_repo.get_last_execution_time.return_value = "2026-07-16T12:00:00Z"
        
        status = self.service.get_status(MagicMock())
        self.assertEqual(status.daily, "SUCCESS")
        self.assertEqual(status.weekly, "FAILED")
        self.assertEqual(status.monthly, "PENDING")
        self.assertEqual(status.running, False)
        
    def test_running_overlap(self):
        self.service._is_running = True
        self.service.run_daily()
        self.mock_repo.create_run.assert_not_called() # Should skip

if __name__ == '__main__':
    unittest.main()
