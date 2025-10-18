from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "ai-ml-strategy-service"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8002

    # CORS (accept CSV or JSON string via env)
    ALLOWED_ORIGINS: str = (
        "http://localhost:3000,https://dev.alphintra.internal,https://api.alphintra.com"
    )

    # Database
    DATABASE_URL: str = "sqlite:///./data/ai_ml_strategy.db"

    # Storage
    STORAGE_MODE: str = "database"  # or "gcs" in future
    GCS_BUCKET_NAME: str | None = None

    # AI Providers (optional, stubs used if missing)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def allowed_origins(self) -> List[str]:
        v = (self.ALLOWED_ORIGINS or "").strip()
        if not v:
            return []
        if v.startswith("[") and v.endswith("]"):
            try:
                data = json.loads(v)
                if isinstance(data, list):
                    return [str(x) for x in data]
            except Exception:
                pass
        return [o.strip() for o in v.split(",") if o.strip()]


settings = Settings()
