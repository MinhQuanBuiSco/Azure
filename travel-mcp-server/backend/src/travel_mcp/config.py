"""Configuration settings for Travel MCP Server."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server settings
    server_name: str = "travel-planner"
    server_version: str = "0.1.0"
    debug: bool = False

    # API Keys for travel services
    serpapi_api_key: str = ""
    openweather_api_key: str = ""
    google_places_api_key: str = ""
    exchangerate_api_key: str = ""

    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    cache_ttl_seconds: int = 3600  # 1 hour default

    # Azure OpenAI settings
    azure_ai_endpoint: str = ""
    azure_ai_key: str = ""
    azure_ai_model: str = "gpt-4o-mini"

    # Azure settings (for deployment)
    azure_client_id: str = ""
    azure_tenant_id: str = ""
    azure_subscription_id: str = ""

    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        # Use rediss:// for SSL (Azure Redis uses port 6380 for SSL)
        scheme = "rediss" if self.redis_port == 6380 else "redis"
        if self.redis_password:
            return f"{scheme}://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"{scheme}://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
