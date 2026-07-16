import hashlib
import json
import logging
from sqlalchemy.orm import Session
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.prompts.classifier_prompt import CLASSIFIER_PROMPT_V1
from backend.domains.ai.classification.classification_models import (
    AIClassificationInput, 
    AIClassificationOutput,
    AIClassificationRecord
)
from backend.domains.ai.classification.classification_repository import ClassificationRepository

logger = logging.getLogger(__name__)

class AIClassificationService:
    def __init__(self, provider: GeminiProvider, repository: ClassificationRepository):
        self.provider = provider
        self.repository = repository

    def _generate_prompt_hash(self, data: AIClassificationInput) -> str:
        # hash: Description + Institution + Approximate Value
        approx_value = round(data.amount, 0)
        raw_string = f"{data.description}|{data.institution}|{approx_value}".lower()
        return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

    def classify_transaction(self, session: Session, transaction_hash: str, data: AIClassificationInput) -> AIClassificationOutput:
        # 1. Ensure table exists (Can be done elsewhere in production, placed here for robustness)
        self.repository.ensure_table_exists(session)

        # 2. Check Cache
        prompt_hash = self._generate_prompt_hash(data)
        cached_record = self.repository.get_cached_classification(session, prompt_hash)
        
        if cached_record:
            logger.info(f"Cache hit for prompt_hash {prompt_hash}")
            return AIClassificationOutput(
                suggested_category=cached_record.suggested_category,
                confidence=cached_record.confidence,
                reason="Cached result",
                alternatives=[]
            )

        # 3. Call AI
        prompt = CLASSIFIER_PROMPT_V1.format(
            description=data.description,
            amount=data.amount
        )
        
        # Build schema template for JSON generation if required
        # For gemini_provider's generate_json, it parses the output text.
        
        prompt_with_schema = prompt + "\nO JSON DEVE CONTER APENAS AS CHAVES: 'suggested_category', 'confidence', 'reason', 'alternatives' (array de strings)."
        
        max_retries = self.provider.config.GEMINI_MAX_RETRIES
        attempts = 0
        last_error = None
        
        while attempts < max_retries:
            try:
                response = self.provider.generate_json(prompt_with_schema)
                if not response.success or not response.data:
                    raise ValueError("Failed to get a valid response from Gemini.")
                
                output_dto = AIClassificationOutput(**response.data)
                
                # Check low confidence
                if output_dto.confidence < 0.80:
                    logger.warning(f"Low confidence AI response: {output_dto.confidence}")
                    # Frontend will ask for confirmation based on this score
                    
                record = AIClassificationRecord(
                    transaction_hash=transaction_hash,
                    prompt_hash=prompt_hash,
                    suggested_category=output_dto.suggested_category,
                    confidence=output_dto.confidence,
                    accepted_by_user=None,
                    final_category=None
                )
                self.repository.save_classification(session, record)
                
                return output_dto
                
            except Exception as e:
                attempts += 1
                last_error = e
                logger.warning(f"Retry {attempts}/{max_retries} failed for classification: {e}")
                
        logger.error(f"All retries failed to classify transaction via AI: {last_error}")
        raise last_error
