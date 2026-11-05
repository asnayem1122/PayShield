"""Application configuration settings for PayShield.

Provides Pydantic Settings-based environment variable parsing with secret
masking and safe SQLAlchemy URL generation for runtime and migration roles.
"""

from pathlib import Path
import secrets
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

# Root of backend directory where .env may reside
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

INSECURE_SECRET_PATTERNS = (
    "insecure",
    "change_this",
    "replace_in_production",
    "default",
    "secret",
    "placeholder",
    "payshielddefault",
    "development_jwt",
    "123456",
)


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
    # Uses ephemeral cryptographic random defaults when unconfigured in development
    SECRET_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32))
    )
    JWT_SECRET_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32))
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "payshield-auth"
    JWT_AUDIENCE: str = "payshield-client"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15
    BCRYPT_ROUNDS: int = 12

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: ["*"]
    )

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        """Harden security parameters: enforce key lengths, reject insecure placeholders, and fail closed in production."""
        is_prod = self.ENVIRONMENT.lower() in ("staging", "production")
        secret_val = self.JWT_SECRET_KEY.get_secret_value()

        if is_prod:
            if not secret_val or len(secret_val) < 32:
                raise ValueError(
                    f"In {self.ENVIRONMENT} environment, JWT_SECRET_KEY must be explicitly configured and at least 32 characters long."
                )
            lower_val = secret_val.lower()
            for pattern in INSECURE_SECRET_PATTERNS:
                if pattern in lower_val:
                    raise ValueError(
                        f"In {self.ENVIRONMENT} environment, JWT_SECRET_KEY cannot contain insecure placeholder '{pattern}'."
                    )
            # In staging/production, fail closed on default database passwords
            app_pw = self.POSTGRES_PASSWORD.get_secret_value()
            mig_pw = self.MIGRATION_POSTGRES_PASSWORD.get_secret_value()
            if "insecure_dev_password" in app_pw or "insecure_dev_password" in mig_pw:
                raise ValueError(
                    f"In {self.ENVIRONMENT} environment, database passwords must not use default insecure development values."
                )
            # In staging/production, fail closed on wildcard CORS
            if "*" in self.CORS_ALLOWED_ORIGINS:
                raise ValueError(
                    f"In {self.ENVIRONMENT} environment, CORS_ALLOWED_ORIGINS cannot contain wildcard '*' when credentials are permitted."
                )
        else:
            if secret_val and len(secret_val) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters long.")

        return self

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
