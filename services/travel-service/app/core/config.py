from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PRODUCTION_ENVIRONMENTS = {"production", "prod"}
PLACEHOLDER_JWT_SECRETS = {
    "change-this-local-dev-secret",
    "replace-with-a-long-random-secret-before-production",
}
LOCAL_ONLY_VALUES = ("localhost", "127.0.0.1", "host.docker.internal")


class Settings(BaseSettings):
    environment: str = "local"
    service_name: str = "travel-service"
    database_url: str = "postgresql+psycopg://travel_service:travel_password@localhost:5434/travel_db"
    jwt_secret_key: str = "change-this-local-dev-secret"
    jwt_algorithm: str = "HS256"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    rate_limit: str = "180/minute"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in PRODUCTION_ENVIRONMENTS

    @model_validator(mode="after")
    def validate_production_settings(self):
        if not self.is_production:
            return self

        if self.jwt_secret_key in PLACEHOLDER_JWT_SECRETS or len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be replaced with a strong production secret")

        if any(value in self.database_url for value in LOCAL_ONLY_VALUES):
            raise ValueError("DATABASE_URL must point to the production database when ENVIRONMENT=production")

        if any(value in origin for origin in self.cors_origin_list for value in LOCAL_ONLY_VALUES):
            raise ValueError("CORS_ORIGINS must contain only production origins when ENVIRONMENT=production")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
