"""API service configuration — loads from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings

# Locate the .env file (project root, above api/)
_v4_env = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "nps"
    postgres_user: str = "nps"
    postgres_password: str = "changeme"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "changeme-generate-a-real-secret"
    api_cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # gRPC backends
    scanner_grpc_host: str = "localhost"
    scanner_grpc_port: int = 50051
    oracle_grpc_host: str = "localhost"
    oracle_grpc_port: int = 50052

    # Encryption
    nps_encryption_key: str = ""
    nps_encryption_salt: str = ""

    # AI / Oracle
    anthropic_api_key: str = ""

    # Telegram
    nps_bot_token: str = ""
    nps_chat_id: str = ""
    telegram_enabled: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Optional override — set DATABASE_URL to skip PostgreSQL entirely
    database_url_override: str = ""

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",")]

    class Config:
        env_file = str(_v4_env) if _v4_env.is_file() else ".env"
        extra = "ignore"


settings = Settings()
