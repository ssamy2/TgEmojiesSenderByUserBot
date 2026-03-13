import os
import secrets
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "Telegram Premium Sender API"
    APP_VERSION: str = "1.0.0"
    
    TELEGRAM_API_ID: int = Field(default=0, description="Telegram API ID from my.telegram.org")
    TELEGRAM_API_HASH: str = Field(default="", description="Telegram API Hash from my.telegram.org")
    
    @property
    def API_ID(self) -> int:
        return self.TELEGRAM_API_ID
    
    @property
    def API_HASH(self) -> str:
        return self.TELEGRAM_API_HASH
    
    API_KEY: Optional[str] = Field(default=None, description="Main API key for authentication")
    API_KEY_FILE: str = "api_key.txt"
    
    SESSIONS_DIR: str = "sessions"
    WORKDIR: str = "."
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    MAX_RETRIES: int = 5
    RETRY_BASE_DELAY: float = 1.0
    RETRY_MAX_DELAY: float = 60.0
    
    RATE_LIMIT_PER_MINUTE: int = 30
    
    class Config:
        env_file = ".env"
        extra = "allow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.API_KEY:
            self._load_or_generate_api_key()

    def _load_or_generate_api_key(self):
        key_file = Path(self.API_KEY_FILE)
        if key_file.exists():
            self.API_KEY = key_file.read_text().strip()
        else:
            self.API_KEY = self._generate_strong_api_key()
            key_file.write_text(self.API_KEY)

    def _generate_strong_api_key(self) -> str:
        return secrets.token_urlsafe(32)

    def get_session_path(self, session_name: str = "main") -> Path:
        session_dir = Path(self.SESSIONS_DIR)
        session_dir.mkdir(exist_ok=True)
        return session_dir / f"{session_name}.session"

    def validate_api_key(self, provided_key: str) -> bool:
        if not self.API_KEY:
            return False
        return secrets.compare_digest(self.API_KEY, provided_key)


settings = Settings()
