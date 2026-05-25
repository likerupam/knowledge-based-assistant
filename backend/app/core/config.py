from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/knowledge_base"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "documents"

    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API
    cors_origins: list[str] = ["*"]
    create_tables_on_startup: bool = True

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 700
    rag_max_context_chars: int = 12000

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Chunking
    chunk_size: int = 1024
    chunk_overlap: int = 128

    # Environment
    environment: str = "development"
    debug: bool = True

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value


settings = Settings()
