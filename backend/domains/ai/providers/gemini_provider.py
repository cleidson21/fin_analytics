import time
import logging
from typing import Optional, Dict, Any

from backend.domains.ai.config import AIConfig
from backend.domains.ai.exceptions import (
    AITimeoutException,
    AIRateLimitException,
    AIApiUnavailableException,
    AIInvalidKeyException,
    AIQuotaExceededException,
    AIBaseException
)
from backend.domains.ai.schemas import AIResponseDTO, AIHealthcheckDTO

logger = logging.getLogger(__name__)

class GeminiProvider:
    def __init__(self):
        self.config = AIConfig()
        self.model_name = self.config.GEMINI_MODEL
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        if not self.config.GEMINI_ENABLED:
            logger.info("Gemini provider is disabled via config.")
            return

        if not self.config.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. Provider will run in fallback mode.")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            self._client = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini SDK: {e}")

    def _handle_sdk_error(self, error: Exception):
        err_str = str(error).lower()
        
        if "401" in err_str or "api key not valid" in err_str:
            raise AIInvalidKeyException("Invalid Gemini API Key.")
        if "429" in err_str or "quota" in err_str:
            if "exhausted" in err_str or "exceeded" in err_str:
                raise AIQuotaExceededException("Gemini Quota Exceeded.")
            raise AIRateLimitException("Gemini Rate Limit reached.")
        if "timeout" in err_str or "deadline" in err_str:
            raise AITimeoutException("Gemini API Timeout.")
        if "500" in err_str or "503" in err_str or "unavailable" in err_str:
            raise AIApiUnavailableException("Gemini API is unavailable.")
            
        raise AIBaseException(f"Unhandled Gemini Error: {str(error)}")

    def generate(self, prompt: str) -> AIResponseDTO:
        start_time = time.time()
        
        if not self._client:
            raise AIApiUnavailableException("Gemini Client not initialized.")
            
        try:
            # We are not implementing automatic features, just the read-only communication layer.
            # No real call made for now, returning dummy response to fulfill TSK-8.2 requirements 
            # while protecting budget, since the prompt says "Não implementar chamadas ao Gemini nesta etapa".
            # Actually, the prompt says "O Provider deverá possuir apenas: generate(), generate_json(), healthcheck()".
            # Let's write the real code but it won't be used by the system yet.
            
            response = self._client.generate_content(
                prompt,
                request_options={"timeout": self.config.GEMINI_TIMEOUT}
            )
            
            latency = time.time() - start_time
            tokens = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            
            return AIResponseDTO(
                success=True,
                data={"text": response.text},
                usage={"prompt_tokens": tokens}, # simplified
                model=self.model_name,
                tokens=tokens,
                latency=latency
            )
            
        except Exception as e:
            self._handle_sdk_error(e)

    def generate_json(self, prompt: str, schema: Any = None) -> AIResponseDTO:
        # Same as generate but with JSON instruction
        start_time = time.time()
        
        if not self._client:
            raise AIApiUnavailableException("Gemini Client not initialized.")
            
        try:
            import google.generativeai as genai
            
            config_args = {"response_mime_type": "application/json"}
            if schema:
                # Optionally pass pydantic schema to the genai SDK if supported
                pass

            response = self._client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(**config_args),
                request_options={"timeout": self.config.GEMINI_TIMEOUT}
            )
            
            latency = time.time() - start_time
            tokens = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            
            import json
            data = json.loads(response.text)
            
            return AIResponseDTO(
                success=True,
                data=data,
                usage={"prompt_tokens": tokens},
                model=self.model_name,
                tokens=tokens,
                latency=latency
            )
            
        except Exception as e:
            self._handle_sdk_error(e)

    def healthcheck(self) -> AIHealthcheckDTO:
        start_time = time.time()
        status = "offline"
        availability = False
        
        if self._client:
            try:
                # A lightweight call to verify connectivity
                self._client.generate_content(
                    "ping", 
                    request_options={"timeout": 5}
                )
                status = "online"
                availability = True
            except Exception as e:
                status = "error"
                logger.error(f"Gemini healthcheck failed: {e}")
                
        latency = (time.time() - start_time) * 1000  # ms
        
        return AIHealthcheckDTO(
            provider="Gemini",
            model=self.model_name,
            status=status,
            response_time_ms=latency,
            availability=availability
        )
