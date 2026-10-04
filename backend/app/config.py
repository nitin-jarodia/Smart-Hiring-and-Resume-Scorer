from pydantic_settings import BaseSettings
from typing import List, Optional
import os

DEV_SECRET_KEY = "dev-secret-key-change-in-production"

class Settings(BaseSettings):
    SECRET_KEY: str = DEV_SECRET_KEY
    DATABASE_URL: str = "sqlite:///./resume_screener.db"
    OPENAI_API_KEY: Optional[str] = None
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    SEED_ADMIN_EMAIL: str = "admin@screener.dev"
    SEED_ADMIN_PASSWORD: Optional[str] = None

    @property
    def is_dev_secret(self) -> bool:
        return self.SECRET_KEY == DEV_SECRET_KEY

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
