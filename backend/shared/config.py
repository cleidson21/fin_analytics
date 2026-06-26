from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    NEXT_PUBLIC_API_URL: str
    SECRET_KEY: str = "secret-key-for-development-only"
    ADMIN_EMAIL: str = "admin@finanalytics.local"
    ADMIN_PASSWORD: str = "admin"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
