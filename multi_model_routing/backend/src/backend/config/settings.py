"""Application settings and configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Multi-Model LLM Router"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Microsoft Foundry (Single account for all models)
    # Base endpoint: https://<resource>.services.ai.azure.com
    foundry_resource_name: str = Field(default="")
    foundry_api_key: SecretStr = Field(default=SecretStr(""))
    foundry_api_version: str = "2025-04-01-preview"

    # Model deployments
    gpt41_deployment: str = "gpt-4.1"
    gpt41_mini_deployment: str = "gpt-4.1-mini"
    gpt41_nano_deployment: str = "gpt-4.1-nano"
    claude_haiku_deployment: str = "claude-haiku-4-5"
    claude_sonnet_deployment: str = "claude-sonnet-4-5"
    claude_opus_deployment: str = "claude-opus-4-5"

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_password: SecretStr = Field(default=SecretStr(""))
    redis_ssl: bool = False

    # Cosmos DB
    cosmos_endpoint: str = Field(default="")
    cosmos_key: SecretStr = Field(default=SecretStr(""))
    cosmos_database: str = "llm_routing"

    # Budget defaults
    default_daily_budget: float = 100.0
    default_weekly_budget: float = 500.0
    default_monthly_budget: float = 2000.0

    # Routing
    complexity_cache_ttl: int = 300  # 5 minutes


    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def foundry_openai_endpoint(self) -> str:
        """Get the OpenAI-compatible endpoint for GPT models."""
        return f"https://{self.foundry_resource_name}.openai.azure.com"



@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
