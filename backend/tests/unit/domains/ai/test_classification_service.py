import unittest
from unittest.mock import MagicMock, patch
from backend.domains.ai.classification.classification_service import AIClassificationService
from backend.domains.ai.classification.classification_models import AIClassificationInput, AIClassificationRecord
from backend.domains.ai.exceptions import AITimeoutException
from backend.domains.ai.schemas import AIResponseDTO
from datetime import date

class TestAIClassificationService(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_provider.config.GEMINI_MAX_RETRIES = 2
        self.mock_repo = MagicMock()
        self.service = AIClassificationService(self.mock_provider, self.mock_repo)
        self.session = MagicMock()
        
        self.input_data = AIClassificationInput(
            description="Uber do Brasil",
            institution="Nubank",
            amount=25.50,
            date=date(2026, 7, 16)
        )

    def test_cache_hit(self):
        # Setup cache hit
        cached_record = AIClassificationRecord(
            transaction_hash="hash_123",
            prompt_hash="mock_prompt_hash",
            suggested_category="Transporte",
            confidence=0.99,
            accepted_by_user=None,
            final_category=None
        )
        self.mock_repo.get_cached_classification.return_value = cached_record
        
        # Act
        result = self.service.classify_transaction(self.session, "hash_123", self.input_data)
        
        # Assert
        self.assertEqual(result.suggested_category, "Transporte")
        self.assertEqual(result.confidence, 0.99)
        self.assertEqual(result.reason, "Cached result")
        self.mock_provider.generate_json.assert_not_called()
        
    def test_high_confidence(self):
        # Setup cache miss
        self.mock_repo.get_cached_classification.return_value = None
        
        mock_response = AIResponseDTO(
            success=True,
            data={"suggested_category": "Transporte", "confidence": 0.95, "reason": "uber", "alternatives": []},
            model="gemini",
            tokens=50,
            latency=0.5
        )
        self.mock_provider.generate_json.return_value = mock_response
        
        # Act
        result = self.service.classify_transaction(self.session, "hash_123", self.input_data)
        
        # Assert
        self.assertEqual(result.suggested_category, "Transporte")
        self.assertEqual(result.confidence, 0.95)
        self.mock_provider.generate_json.assert_called_once()
        self.mock_repo.save_classification.assert_called_once()

    def test_low_confidence(self):
        # Setup cache miss
        self.mock_repo.get_cached_classification.return_value = None
        
        mock_response = AIResponseDTO(
            success=True,
            data={"suggested_category": "Outros", "confidence": 0.60, "reason": "unknown", "alternatives": ["Alimentação"]},
            model="gemini",
            tokens=50,
            latency=0.5
        )
        self.mock_provider.generate_json.return_value = mock_response
        
        # Act
        result = self.service.classify_transaction(self.session, "hash_123", self.input_data)
        
        # Assert
        self.assertEqual(result.suggested_category, "Outros")
        self.assertEqual(result.confidence, 0.60) # Below 0.80

    def test_invalid_response_triggers_retry(self):
        self.mock_repo.get_cached_classification.return_value = None
        
        invalid_response = AIResponseDTO(success=False, model="gemini", tokens=10, latency=0.1)
        valid_response = AIResponseDTO(
            success=True,
            data={"suggested_category": "Saúde", "confidence": 0.90, "reason": "farma", "alternatives": []},
            model="gemini",
            tokens=50,
            latency=0.5
        )
        
        # First call invalid, second valid
        self.mock_provider.generate_json.side_effect = [invalid_response, valid_response]
        
        # Act
        result = self.service.classify_transaction(self.session, "hash_123", self.input_data)
        
        # Assert
        self.assertEqual(self.mock_provider.generate_json.call_count, 2)
        self.assertEqual(result.suggested_category, "Saúde")

    def test_timeout_and_retry_exhausted(self):
        self.mock_repo.get_cached_classification.return_value = None
        
        # Provider always throws AITimeoutException
        self.mock_provider.generate_json.side_effect = AITimeoutException("Timeout")
        
        # Act & Assert
        with self.assertRaises(AITimeoutException):
            self.service.classify_transaction(self.session, "hash_123", self.input_data)
            
        self.assertEqual(self.mock_provider.generate_json.call_count, 2) # max_retries = 2

if __name__ == '__main__':
    unittest.main()
