# marketplace/config.py

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables (including .env file).
    """
    DATABASE_URL: str
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    DOMAIN_URL: str

    class Config:
        # Load environment variables from a .env file in the same directory as this file
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        # Enable case-insensitive match for env variables
        case_sensitive = True

# Create a settings instance to be imported across the app
settings = Settings()
