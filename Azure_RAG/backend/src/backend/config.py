from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "RAG Application"
    app_version: str = "1.0.0"
    debug: bool = False
    frontend_url: Optional[str] = None  # Set via FRONTEND_URL env var

    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins including dynamic frontend URL"""
        origins = [
            "http://localhost:3000",
            "http://localhost:5173",
        ]
        # Add production frontend URL if set
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        return origins

    # Azure Blob Storage
    azure_storage_connection_string: Optional[str] = None
    azure_storage_account_name: Optional[str] = None
    azure_storage_container_name: str = "pdfs"

    # Azure AI Search
    azure_search_endpoint: Optional[str] = None
    azure_search_api_key: Optional[str] = None
    azure_search_index_name: str = "rag-index"

    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    azure_openai_chat_deployment: str = "gpt-4o-mini"
    azure_openai_embedding_dimensions: int = 1536

    # Redis Cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_ssl: bool = False
    cache_ttl: int = 3600  # 1 hour

    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 50

    # Search Settings
    default_top_k: int = 5
    max_top_k: int = 20

    # Entity Extraction
    entity_extraction_enabled: bool = True
    entity_types: list[str] = [
        "people",
        "organizations",
        "locations",
        "dates",
        "topics",
        "technical_terms"
    ]


# Global settings instance
settings = Settings()
