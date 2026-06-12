"""
Application settings loaded from environment variables / .env file.
pydantic-settings auto-reads .env and validates types.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://secai:secai@postgres:5432/secai"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Auth
    SECRET_KEY: str = "change-this-to-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8

    # ChromaDB — backend connects on container-internal port 8000
    CHROMADB_HOST: str = "chromadb"
    CHROMADB_PORT: int = 8000

    # Ollama — runs on host, not inside Docker
    OLLAMA_HOST: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "mistral"

    # File storage
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Single shared instance — import this everywhere instead of instantiating Settings()
settings = Settings()