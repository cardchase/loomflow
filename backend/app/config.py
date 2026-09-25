from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DEFAULT_LLM_PROVIDER: str = "local"
    LOCAL_LLM_BASE_URL: str = "http://localhost:1234/v1"
    LOCAL_LLM_MODEL: str = "local-model"
    LOCAL_LLM_API_KEY: str = "not-needed"
    GEMINI_API_KEY: Optional[str] = Field(default=None, validation_alias="GOOGLE_API_KEY")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
