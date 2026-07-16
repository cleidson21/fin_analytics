import logging
from backend.domains.ai.providers.gemini_provider import GeminiProvider
from backend.domains.ai.schemas import AIResponseDTO, AIHealthcheckDTO

logger = logging.getLogger(__name__)

class AIService:
    """
    Orchestration layer for AI. Currently only exposes basic provider capabilities
    to comply with TSK-8.2 requirements. No automations or business logic implemented yet.
    """
    def __init__(self, provider: GeminiProvider = None):
        self.provider = provider or GeminiProvider()
        
    def check_health(self) -> AIHealthcheckDTO:
        return self.provider.healthcheck()
        
    def basic_generate(self, prompt: str) -> AIResponseDTO:
        return self.provider.generate(prompt)
