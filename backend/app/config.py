import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = False
    
    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "german_learning"
    
    # File storage
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 50
    STORAGE_PROVIDER: str = "local"
    S3_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_REGION: str = "auto"
    S3_PRESIGNED_URL_SECONDS: int = 300
    
    # AI & Speech
    AI_PROVIDER: str = "disabled"
    AI_API_BASE_URL: Optional[str] = None
    AI_API_KEY: Optional[str] = None
    AI_MODEL: Optional[str] = None
    AI_EMBED_MODEL: Optional[str] = None
    OLLAMA_BASE_URL: Optional[str] = None
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT_SECONDS: float = 180.0
    STT_PROVIDER: str = "browser"
    TTS_PROVIDER: str = "browser"
    
    # RAG & Retrieval
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 100
    RAG_MAX_CHUNKS: int = 4
    RAG_SIMILARITY_THRESHOLD: float = 0.12
    CHAT_MAX_HISTORY_MESSAGES: int = 10
    CHAT_MAX_MESSAGE_LENGTH: int = 2000
    
    # Security & CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    SESSION_COOKIE_NAME: str = "deutsch_session"
    SESSION_TTL_DAYS: int = 14

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
if settings.APP_ENV.lower() == "production":
    if not settings.MONGODB_URI or "localhost" in settings.MONGODB_URI or "127.0.0.1" in settings.MONGODB_URI:
        raise RuntimeError("Production requires a remote MongoDB connection through MONGODB_URI.")
    if settings.AI_PROVIDER.lower() == "ollama":
        raise RuntimeError("Production cannot use a local Ollama provider. Configure a hosted provider or disable AI.")
    if settings.STORAGE_PROVIDER.lower() not in {"s3", "r2", "s3-compatible"}:
        raise RuntimeError("Production requires S3-compatible persistent file storage.")
    if "*" in settings.cors_origin_list:
        raise RuntimeError("Production CORS must use explicit frontend origins.")
    if not settings.cors_origin_list or any("localhost" in origin or "127.0.0.1" in origin for origin in settings.cors_origin_list):
        raise RuntimeError("Production CORS_ORIGINS must contain the deployed frontend origin.")
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
