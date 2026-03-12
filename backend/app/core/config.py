"""TravManager — Application Configuration"""
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://travmanager:travmanager_dev_2024@db:5432/travmanager"
    DATABASE_URL_SYNC: str = "postgresql://travmanager:travmanager_dev_2024@db:5432/travmanager"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Auth
    SECRET_KEY: str = "change-me-in-production-travmanager-2024"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # App
    APP_NAME: str = "TravManager"
    APP_ENV: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Game constants (in öre: 1 kr = 100 öre)
    STARTING_BALANCE: int = 20_000_000  # 200 000 kr
    NPC_MIN_FIELD_SIZE: int = 8
    NPC_MAX_FIELD_SIZE: int = 12

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def fix_database_url(self):
        """Railway provides postgres:// — convert to asyncpg format."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            self.DATABASE_URL = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            self.DATABASE_URL = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self


settings = Settings()
