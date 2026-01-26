"""Application configuration using Pydantic Settings."""

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    AZURE_OPENAI = "azure_openai"
    AZURE_ANTHROPIC = "azure_anthropic"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Finance Research Pipeline"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # LLM Provider Selection
    llm_provider: LLMProvider = LLMProvider.AZURE_OPENAI

    # Azure OpenAI
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: SecretStr | None = None
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_api_version: str = "2024-08-01-preview"

    # Azure AI Foundry (Anthropic)
    azure_ai_foundry_endpoint: str | None = None
    azure_ai_foundry_api_key: SecretStr | None = None
    azure_ai_foundry_model: str = "claude-3-5-sonnet"

    # Direct OpenAI (fallback)
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o"

    # Direct Anthropic (fallback)
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # Tools
    tavily_api_key: SecretStr | None = None
    newsapi_key: SecretStr | None = None

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: SecretStr | None = None
    redis_db: int = 0
    redis_ssl: bool = False
    cache_ttl_seconds: int = 3600  # 1 hour default

    # Cosmos DB
    cosmos_endpoint: str | None = None
    cosmos_key: SecretStr | None = None
    cosmos_database: str = "finance_research"
    cosmos_container_sessions: str = "sessions"
    cosmos_container_reports: str = "reports"

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

    @property
    def redis_url(self) -> str:
        """Build Redis connection URL."""
        protocol = "rediss" if self.redis_ssl else "redis"
        if self.redis_password:
            return f"{protocol}://:{self.redis_password.get_secret_value()}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"{protocol}://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
