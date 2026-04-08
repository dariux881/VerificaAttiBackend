# backend/app/core/config.py
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
import os
from functools import lru_cache

class Settings(BaseSettings):
    # App
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")

    ALLOWED_HOSTS: List[str] = Field(default=["*"], validation_alias="ALLOWED_HOSTS")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        validation_alias="CORS_ORIGINS"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    DOCUMENT_BASE_PATH: str = Field(default=r".\atti", validation_alias="DOCUMENT_BASE_PATH")
    SOURCES_BASE_PATH: str = Field(default=r".\external_sources", validation_alias="SOURCES_BASE_PATH")

    HEALTH_CHECK_INTERVAL_SECONDS: int = Field(default=300, validation_alias="HEALTH_CHECK_INTERVAL_SECONDS")
    
    VERIFICA_ATTI_WEBHOOK_URL: str = Field(default="", validation_alias="VERIFICA_ATTI_WEBHOOK_URL")

    DATABASE_URL: str = Field(default="", validation_alias="DATABASE_URL")

    SECRET_KEY: str = Field(default="", validation_alias="JWT_SECRET_KEY")
    ALGORITHM: str = Field(default="", validation_alias="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: float = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: float = Field(default=7, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")

    PORT: int = Field(default=8000, validation_aliases=AliasChoices("PORT", "APP_PORT"))
    HOST: str = Field(default="0.0.0.0", validation_alias="HOST")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

