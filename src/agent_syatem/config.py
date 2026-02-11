from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Project
    PROJECT_NAME: str = "Multi-Agent System"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DEBUG: bool = Field(False, env="DEBUG")
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = DATA_DIR / "logs"
    TEMP_DIR: Path = DATA_DIR / "temp"
    MEMORY_DIR: Path = DATA_DIR / "memory"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_URL")
    TELEGRAM_PORT: int = Field(8080, env="TELEGRAM_PORT")
    
    # Ollama
    OLLAMA_HOST: str = Field("http://localhost:11434", env="OLLAMA_HOST")
    OLLAMA_TIMEOUT: int = Field(120, env="OLLAMA_TIMEOUT")
    DEFAULT_MODEL: str = Field("phi4:14b", env="DEFAULT_MODEL")
    
    # Email
    IMAP_SERVER: str = Field("imap.gmail.com", env="IMAP_SERVER")
    SMTP_SERVER: str = Field("smtp.gmail.com", env="SMTP_SERVER")
    EMAIL_ADDRESS: Optional[str] = Field(None, env="EMAIL_ADDRESS")
    EMAIL_PASSWORD: Optional[str] = Field(None, env="EMAIL_PASSWORD")
    EMAIL_CHECK_INTERVAL: int = Field(300, env="EMAIL_CHECK_INTERVAL")  # 5 minutes
    
    # Redis
    REDIS_URL: str = Field("redis://localhost:6379", env="REDIS_URL")
    REDIS_TTL: int = Field(3600, env="REDIS_TTL")  # 1 hour
    
    # Search
    SEARCH_API_KEY: Optional[str] = Field(None, env="SEARCH_API_KEY")
    SEARCH_ENGINE: str = Field("duckduckgo", env="SEARCH_ENGINE")
    
    # Model Configuration
    MODEL_TIERS: Dict[str, List[str]] = {
        "essential": [
            "gemma3:1b",
            "gemma3:4b",
            "qwen2.5-coder:3b",
            "qwen2.5-coder:7b",
            "phi4:14b"
        ],
        "extended": [
            "llama3.2-vision:11b",
            "minicpm-v:8b",
            "aya:8b",
            "nous-hermes2:10.7b",
            "mistral-nemo:12b",
            "qwen2.5:14b"
        ],
        "maximum": [
            "gemma3:12b",
            "qwen2.5:32b",
            "deepseek-coder-v2:16b",
            "command-r:35b"
        ]
    }
    
    # Model Registry
    MODEL_CAPABILITIES: Dict[str, Dict] = {
        "gemma3:1b": {"speed": 5, "quality": 2, "vram": 1, "type": "router"},
        "gemma3:4b": {"speed": 4, "quality": 3, "vram": 3, "type": "vision"},
        "qwen2.5-coder:3b": {"speed": 4, "quality": 3, "vram": 2.5, "type": "code"},
        "qwen2.5-coder:7b": {"speed": 3, "quality": 4, "vram": 5, "type": "code"},
        "phi4:14b": {"speed": 2, "quality": 5, "vram": 10, "type": "analysis"},
        "llama3.2-vision:11b": {"speed": 2, "quality": 4, "vram": 8, "type": "vision"},
        "aya:8b": {"speed": 3, "quality": 4, "vram": 6, "type": "synthesis"},
        "deepseek-coder-v2:16b": {"speed": 2, "quality": 5, "vram": 12, "type": "code"}
    }
    
    # Agent Settings
    MAX_CONVERSATION_HISTORY: int = Field(10, env="MAX_CONVERSATION_HISTORY")
    CODE_EXECUTION_TIMEOUT: int = Field(30, env="CODE_EXECUTION_TIMEOUT")
    MAX_EMAILS_PER_CHECK: int = Field(20, env="MAX_EMAILS_PER_CHECK")
    
    # Performance
    WORKER_COUNT: int = Field(4, env="WORKER_COUNT")
    REQUEST_TIMEOUT: int = Field(60, env="REQUEST_TIMEOUT")
    CACHE_TTL: int = Field(300, env="CACHE_TTL")
    
    @field_validator("TELEGRAM_BOT_TOKEN")
    @classmethod
    def validate_telegram_token(cls, v: str) -> str:
        if not v or len(v) < 10:
            raise ValueError("Invalid Telegram bot token")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
