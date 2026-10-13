"""Application settings loaded from environment variables and the .env file."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime settings. Every value can be overridden in .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ECHO"
    log_level: str = "INFO"

    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = "openai/gpt-oss-120b"

    embedding_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    embedding_api_key: SecretStr = SecretStr("")
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768
    embedding_passage_task: str = "retrieval.passage"
    embedding_query_task: str = "retrieval.query"
    embedding_batch_size: int = 32

    deepgram_api_key: SecretStr = SecretStr("")
    deepgram_stt_model: str = "nova-3"
    deepgram_tts_model: str = "aura-2-thalia-en"

    qdrant_url: str = ""
    qdrant_api_key: SecretStr = SecretStr("")
    qdrant_collection: str = "echo_chunks"

    database_url: str = "sqlite+aiosqlite:///./echo.db"

    max_upload_mb: int = 20
    chunk_lines: int = 6
    chunk_overlap_lines: int = 2


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
