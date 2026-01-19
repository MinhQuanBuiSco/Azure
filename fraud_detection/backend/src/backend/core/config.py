"""
Application configuration using Pydantic Settings.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # App Config
    app_name: str = "Fraud Detection API"
    app_version: str = "0.1.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fraud_detection"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    # Azure Cosmos DB
    cosmos_endpoint: Optional[str] = None
    cosmos_key: Optional[str] = None
    cosmos_database: str = "fraud_detection"
    cosmos_container: str = "transactions"

    # Azure Event Hubs
    event_hub_connection_string: Optional[str] = None
    event_hub_name: str = "fraud-transactions"

    # Azure Blob Storage
    storage_account_connection_string: Optional[str] = None
    storage_container_name: str = "fraud-data"

    # Azure Anomaly Detector
    anomaly_detector_endpoint: Optional[str] = None
    anomaly_detector_key: Optional[str] = None

    # Azure AI Foundry (for Claude)
    azure_ai_endpoint: Optional[str] = None
    azure_ai_key: Optional[str] = None
    azure_ai_model_name: str = "claude-3-5-sonnet"  # or claude-3-haiku, claude-3-opus

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Fraud Detection Thresholds
    low_risk_threshold: float = 30.0
    high_risk_threshold: float = 70.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
