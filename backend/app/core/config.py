"""Application configuration settings for PayShield.

Provides Pydantic Settings-based environment variable parsing with secret
masking and safe SQLAlchemy URL generation for runtime and migration roles.
"""

from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

# Root of backend directory where .env may reside
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """PayShield backend settings."""

    # Project metadata
    PROJECT_NAME: str = "PayShield"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # PostgreSQL Server Connection
    POSTGRES_SERVER: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "payshield_dev"

    # Runtime Application Role (payshield_app: DML only)
    POSTGRES_USER: str = "payshield_app"
    POSTGRES_PASSWORD: SecretStr = Field(
        default=SecretStr("payshield_app_insecure_dev_password")
    )

    # Migration Role (payshield_migrator: DDL schema owner)
    MIGRATION_POSTGRES_USER: str = "payshield_migrator"
    MIGRATION_POSTGRES_PASSWORD: SecretStr = Field(
        default=SecretStr("payshield_migrator_insecure_dev_password")
    )

    # Direct URL overrides (e.g. for testing with SQLite or external URI)
    DATABASE_URL_OVERRIDE: SecretStr | None = None
    MIGRATION_DATABASE_URL_OVERRIDE: SecretStr | None = None

    # Connection pool configuration
    DB_POOL_PRE_PING: bool = True
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Security & JWT Configuration
    SECRET_KEY: SecretStr = Field(
        default=SecretStr("payshield_development_jwt_secret_key_minimum_32_bytes_long_for_hs256!")
    )
    JWT_SECRET_KEY: SecretStr = Field(
        default=SecretStr("payshield_development_jwt_secret_key_minimum_32_bytes_long_for_hs256!")
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "payshield-auth"
    JWT_AUDIENCE: str = "payshield-client"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15
    BCRYPT_ROUNDS: int = 12

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def get_sqlalchemy_url(self) -> URL:
        """Generate safe SQLAlchemy connection URL for runtime application role (payshield_app)."""
        if self.DATABASE_URL_OVERRIDE:
            return make_url(self.DATABASE_URL_OVERRIDE.get_secret_value())

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    def get_migration_sqlalchemy_url(self) -> URL:
        """Generate safe SQLAlchemy connection URL for migration role (payshield_migrator)."""
        if self.MIGRATION_DATABASE_URL_OVERRIDE:
            return make_url(self.MIGRATION_DATABASE_URL_OVERRIDE.get_secret_value())

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.MIGRATION_POSTGRES_USER,
            password=self.MIGRATION_POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )


settings = Settings()
