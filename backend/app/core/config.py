"""
Configuration settings for the application
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Smart Travel System API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database - Cloud SQL
    DATABASE_URL: str = "sqlite+aiosqlite:///./smart_travel.db"
    CLOUD_SQL_CONNECTION_NAME: str = ""
    DB_USER: str = "appuser"
    DB_PASS: str = ""
    DB_NAME: str = "smarttravel"
    
    # JWT Authentication
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email / OTP (Brevo SMTP)
    EMAIL_FROM: str = ""
    EMAIL_FROM_NAME: str = "Smart Travel"
    BREVO_API_KEY: str = ""
    BREVO_SMTP_HOST: str = "smtp-relay.brevo.com"
    BREVO_SMTP_PORT: int = 587
    BREVO_SMTP_USER: str = ""
    BREVO_SMTP_PASSWORD: str = ""

    OTP_TTL_MIN: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_LIMIT_PER_HOUR: int = 5
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://smart-travel-frontend-85676926926.asia-southeast1.run.app,https://habi.software"
    
    @property
    def cors_origins_list(self) -> List[str]:
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        # Also allow all origins in production for flexibility
        return origins + ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
