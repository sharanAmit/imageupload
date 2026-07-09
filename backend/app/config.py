import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Set, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Trip Memories Platform"
    
    # Google OAuth ID (set in .env for Sign in with Google)
    GOOGLE_CLIENT_ID: Optional[str] = None

    
    # Database Settings
    # Default to a local postgres database. If postgres is not available, local SQLite can be configured.
    # Note: For production and direct request specs, we configure PostgreSQL.
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/trip_memories"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def format_db_url(cls, v: str) -> str:
        # Automatically use pg8000 dialect for postgresql URLs to avoid compilation requirements
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+pg8000://", 1)
        return v


    
    # JWT Auth Settings
    JWT_SECRET_KEY: str = "supersecretkeychangeinproduction1234567890"
    JWT_REFRESH_SECRET_KEY: str = "supersecretrefreshkeychangeinproduction1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # SMTP Email Settings (Set in .env for actual email delivery)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@tripmemories.local"
    
    # Storage settings
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
    
    # Media constraints
    ALLOWED_IMAGE_EXTENSIONS: Set[str] = {"jpg", "jpeg", "png", "gif", "webp", "heic", "heif"}
    ALLOWED_VIDEO_EXTENSIONS: Set[str] = {"mp4", "mov", "avi", "mkv", "webm"}
    MAX_FILE_SIZE_MB: int = 100  # 100 MB limits
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
