from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # OpenRouter
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL: str = "anthropic/claude-sonnet-4-20250514"
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/biosecurity.db"
    
    # App
    APP_NAME: str = "Biosecurity Threat Forecaster"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()