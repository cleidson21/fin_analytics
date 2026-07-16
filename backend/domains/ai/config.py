import os

class AIConfig:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "15"))
    GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
    GEMINI_ENABLED = os.getenv("GEMINI_ENABLED", "true").lower() == "true"
