"""
Application configuration management
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Core settings
    app_name: str = "Excel Mock Interviewer"
    debug: bool = False
    mock_mode: bool = False
    
    # Database
    database_url: Optional[str] = None
    
    # Redis for job queue
    redis_url: Optional[str] = None
    
    # LLM API keys
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # File storage
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Evaluation settings
    deterministic_weight: float = 0.6
    llm_weight: float = 0.4
    pass_threshold: float = 2.5
    flag_confidence_threshold: float = 0.45
    
    # Interview settings
    max_questions: int = 6
    default_time_limit: int = 300  # 5 minutes per question
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)

# Mock mode auto-detection
if not settings.groq_api_key and not settings.openai_api_key:
    settings.mock_mode = True
    print("⚠️  No LLM API keys found - running in MOCK_MODE")
