import unittest
from unittest.mock import patch, MagicMock
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.exceptions import (
    AITimeoutException,
    AIRateLimitException,
    AIInvalidKeyException,
    AIQuotaExceededException,
    AIApiUnavailableException,
    AIBaseException
)

class TestGeminiProvider(unittest.TestCase):
    @patch('backend.domains.ai.config.AIConfig')
    def setUp(self, mock_config):
        self.mock_config_instance = mock_config.return_value
        self.mock_config_instance.GEMINI_ENABLED = True
        self.mock_config_instance.GEMINI_API_KEY = "test_key"
        self.mock_config_instance.GEMINI_MODEL = "test_model"
        self.mock_config_instance.GEMINI_TIMEOUT = 10
        
        # Patch the genai module so it doesn't initialize actual SDK network
        with patch('backend.domains.ai.providers.gemini_provider.genai', create=True) as mock_genai:
            self.mock_genai = mock_genai
            self.provider = GeminiProvider()
            self.provider._client = MagicMock()

    def test_healthcheck_success(self):
        # Setup
        self.provider._client.generate_content.return_value = MagicMock()
        
        # Act
        result = self.provider.healthcheck()
        
        # Assert
        self.assertEqual(result.status, "online")
        self.assertTrue(result.availability)
        self.assertEqual(result.provider, "Gemini")

    def test_healthcheck_failure(self):
        # Setup
        self.provider._client.generate_content.side_effect = Exception("Network error")
        
        # Act
        result = self.provider.healthcheck()
        
        # Assert
        self.assertEqual(result.status, "error")
        self.assertFalse(result.availability)

    def test_generate_success(self):
        # Setup
        mock_response = MagicMock()
        mock_response.text = "Hello World"
        mock_response.usage_metadata.total_token_count = 10
        self.provider._client.generate_content.return_value = mock_response
        
        # Act
        result = self.provider.generate("Say hello")
        
        # Assert
        self.assertTrue(result.success)
        self.assertEqual(result.data["text"], "Hello World")
        self.assertEqual(result.tokens, 10)

    def test_timeout_exception(self):
        # Setup
        self.provider._client.generate_content.side_effect = Exception("Deadline exceeded")
        
        # Act & Assert
        with self.assertRaises(AITimeoutException):
            self.provider.generate("Say hello")

    def test_rate_limit_exception(self):
        # Setup
        self.provider._client.generate_content.side_effect = Exception("HTTP 429 Too Many Requests")
        
        # Act & Assert
        with self.assertRaises(AIRateLimitException):
            self.provider.generate("Say hello")

    def test_invalid_key_exception(self):
        # Setup
        self.provider._client.generate_content.side_effect = Exception("API key not valid")
        
        # Act & Assert
        with self.assertRaises(AIInvalidKeyException):
            self.provider.generate("Say hello")
            
    def test_quota_exceeded_exception(self):
        # Setup
        self.provider._client.generate_content.side_effect = Exception("Quota exceeded")
        
        # Act & Assert
        with self.assertRaises(AIQuotaExceededException):
            self.provider.generate("Say hello")

if __name__ == '__main__':
    unittest.main()
