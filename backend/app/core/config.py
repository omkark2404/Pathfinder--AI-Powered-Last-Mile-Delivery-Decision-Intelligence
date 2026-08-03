import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from typing import Optional, List


class Settings(BaseSettings):
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )

    PROJECT_NAME: str = "Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence"
    API_V1_STR: str = "/api/v1"

    # SECRET_KEY: used for session signing and HMAC verification.
    # Must be set to a strong random value in production.
    SECRET_KEY: str = "supersecretkey_change_in_production_32bytes!"

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "lastmile_db"

    DATABASE_URL: Optional[str] = None

    # CORS: comma-separated list of allowed origins.
    # Default "*" is only suitable for local development.
    # In production set ALLOWED_ORIGINS=https://your-domain.com
    ALLOWED_ORIGINS: str = "*"

    DATA_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
    )

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def get_allowed_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list for CORSMiddleware."""
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    def is_default_secret_key(self) -> bool:
        """Returns True when the insecure default SECRET_KEY is in use."""
        return self.SECRET_KEY == "supersecretkey_change_in_production_32bytes!"


settings = Settings()
