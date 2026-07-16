import unittest
from unittest.mock import MagicMock, patch
import os
import time

from backend.domains.market_data.scheduler import MarketDataScheduler

class TestMarketDataScheduler(unittest.TestCase):
    @patch.dict(os.environ, {"MARKET_DATA_ENABLED": "true", "MARKET_DATA_INTERVAL": "60", "MARKET_DATA_STARTUP_SYNC": "true"})
    def test_scheduler_initialization(self):
        mock_service = MagicMock()
        scheduler = MarketDataScheduler(mock_service)
        
        self.assertTrue(scheduler.enabled)
        self.assertEqual(scheduler.interval_minutes, 60)
        self.assertTrue(scheduler.startup_sync)
        
    @patch.dict(os.environ, {"MARKET_DATA_ENABLED": "false"})
    def test_scheduler_disabled(self):
        mock_service = MagicMock()
        scheduler = MarketDataScheduler(mock_service)
        
        # Act
        scheduler.start()
        
        # Assert
        self.assertFalse(scheduler._scheduler.running)
        
    @patch('backend.domains.market_data.scheduler.Session')
    @patch.dict(os.environ, {"MARKET_DATA_ENABLED": "true", "MARKET_DATA_STARTUP_SYNC": "false"})
    def test_scheduler_run_sync_success(self, MockSession):
        mock_session = MagicMock()
        MockSession.return_value = mock_session
        
        mock_service = MagicMock()
        mock_service.update_market_data.return_value = {
            "status": "success",
            "tickers_fetched": 2,
            "prices_saved": 2
        }
        
        scheduler = MarketDataScheduler(mock_service)
        result = scheduler.run_sync()
        
        # Assert
        mock_service.update_market_data.assert_called_once_with(mock_session)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        
        self.assertEqual(result["status"], "success")

    @patch('backend.domains.market_data.scheduler.Session')
    def test_scheduler_run_sync_exception_fallback(self, MockSession):
        mock_session = MagicMock()
        MockSession.return_value = mock_session
        
        mock_service = MagicMock()
        mock_service.update_market_data.side_effect = Exception("Yahoo Finance Timeout")
        
        scheduler = MarketDataScheduler(mock_service)
        result = scheduler.run_sync()
        
        # Assert fallback is executed properly
        mock_service.update_market_data.assert_called_once_with(mock_session)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Timeout", result["message"])

if __name__ == '__main__':
    unittest.main()
