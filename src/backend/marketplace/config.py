# marketplace/config.py

from __future__ import annotations

import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Marketplace service configuration.

    All values can be overridden via environment variables. For example:
      export DATABASE_URL=postgresql://user:pass@host:5432/dbname
      export MARKETPLACE_SEED_DEMO_DATA=false
    """

    database_url: str = Field(
        default="postgresql://alphintra:alphintra123@postgres:5432/marketplace",
        alias="DATABASE_URL",
    )
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://localhost:5173",
        ],
        alias="MARKETPLACE_CORS_ORIGINS",
    )
    seed_demo_data: bool = Field(default=True, alias="MARKETPLACE_SEED_DEMO_DATA")

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True


settings = Settings()
