"""Application settings and configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment (accepts both short and long forms)
    environment: Literal["dev", "development", "stg", "staging", "prod", "production"] = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS - Allow all origins for flexibility (configure specific origins in production if needed)
    cors_origins: list[str] = Field(default=["*"])

    # Azure AI Foundry
    azure_ai_endpoint: str = ""
    azure_ai_api_key: str = ""
    azure_ai_deployment_name: str = "gpt-4o"
    azure_ai_api_version: str = "2024-10-21"

    # Azure Content Safety
    azure_content_safety_endpoint: str = ""
    azure_content_safety_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Cosmos DB
    cosmos_connection_string: str = ""
    cosmos_database_name: str = "security_gateway"
    cosmos_container_name: str = "audit_logs"

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Security Settings
    enable_prompt_injection_detection: bool = True
    enable_pii_detection: bool = True
    enable_secret_scanning: bool = True
    enable_content_filtering: bool = True
    enable_jailbreak_detection: bool = True

    # PII Settings
    pii_action: Literal["mask", "block", "log"] = "mask"
    pii_entities_to_detect: list[str] = Field(
        default=[
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "US_SSN",
            "US_BANK_NUMBER",
            "IP_ADDRESS",
        ]
    )

    # Logging
    log_level: str = "INFO"
    log_requests: bool = True
    log_responses: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
