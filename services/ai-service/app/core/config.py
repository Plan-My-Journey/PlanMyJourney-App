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
    service_name: str = "ai-service"
    log_level: str = "info"
    aws_region: str = "us-east-1"
    # AWS Bedrock — credentials come from IAM (IRSA in EKS)
    bedrock_model_id: str = "amazon.nova-pro-v1:0"
    bedrock_region: str = "us-east-1"
    bedrock_max_tokens: int = 1024
    jwt_secret_key: str = "change-this-local-dev-secret"
    jwt_algorithm: str = "HS256"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    rate_limit: str = "90/minute"
    sqs_queue_url: str = ""
    jobs_table_name: str = ""
    async_jobs_enabled: bool = False
    worker_mode: bool = False

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

        if any(value in origin for origin in self.cors_origin_list for value in LOCAL_ONLY_VALUES):
            raise ValueError("CORS_ORIGINS must contain only production origins when ENVIRONMENT=production")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
