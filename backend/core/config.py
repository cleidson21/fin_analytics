from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./database/fin_analytics.db"
    
    # Security
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60
    
    # Integrations
    PIERRE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    MYPROFIT_USERNAME: Optional[str] = None
    MYPROFIT_PASSWORD: Optional[str] = None
    YFINANCE_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

settings = Settings()
