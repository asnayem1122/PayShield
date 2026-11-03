"""Tests for configuration architecture, URL generation, and secret masking."""

import pytest
from pydantic import SecretStr, ValidationError
from sqlalchemy.engine import make_url

from app.core.config import Settings


def test_default_runtime_and_migration_urls() -> None:
    """Verify default URL construction for payshield_app and payshield_migrator."""
    custom_settings = Settings(
        POSTGRES_SERVER="127.0.0.1",
        POSTGRES_PORT=5432,
        POSTGRES_DB="payshield_dev",
        POSTGRES_USER="payshield_app",
        POSTGRES_PASSWORD=SecretStr("app_secret_123"),
        MIGRATION_POSTGRES_USER="payshield_migrator",
        MIGRATION_POSTGRES_PASSWORD=SecretStr("migrator_secret_456"),
    )

    app_url = custom_settings.get_sqlalchemy_url()
    assert app_url.drivername == "postgresql+psycopg"
    assert app_url.username == "payshield_app"
    assert app_url.password == "app_secret_123"
    assert app_url.host == "127.0.0.1"
    assert app_url.port == 5432
    assert app_url.database == "payshield_dev"

    migrator_url = custom_settings.get_migration_sqlalchemy_url()
    assert migrator_url.drivername == "postgresql+psycopg"
    assert migrator_url.username == "payshield_migrator"
    assert migrator_url.password == "migrator_secret_456"
    assert migrator_url.host == "127.0.0.1"
    assert migrator_url.port == 5432
    assert migrator_url.database == "payshield_dev"


def test_database_url_override() -> None:
    """Verify DATABASE_URL_OVERRIDE and MIGRATION_DATABASE_URL_OVERRIDE parsing via make_url."""
    override_url = "postgresql+psycopg://override_user:override_pass@customhost:5433/override_db"
    settings_with_override = Settings(
        DATABASE_URL_OVERRIDE=SecretStr(override_url),
        MIGRATION_DATABASE_URL_OVERRIDE=SecretStr(override_url),
    )

    app_url = settings_with_override.get_sqlalchemy_url()
    assert app_url == make_url(override_url)
    assert app_url.username == "override_user"
    assert app_url.host == "customhost"
    assert app_url.port == 5433

    mig_url = settings_with_override.get_migration_sqlalchemy_url()
    assert mig_url == make_url(override_url)


def test_password_with_reserved_characters() -> None:
    """Verify password with reserved characters is handled safely without corrupting connection parameters."""
    special_password = "p@ss:w/ord#1?&="
    settings_special = Settings(
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD=SecretStr(special_password),
    )

    url = settings_special.get_sqlalchemy_url()
    assert url.password == special_password
    # URL string render handles percent encoding
    rendered = url.render_as_string(hide_password=False)
    assert "test_user" in rendered
    assert "p%40ss%3Aw/ord%231%3F%26=" in rendered or "@test_user" not in rendered


def test_secret_masking() -> None:
    """Verify that repr(settings) and model_dump do not expose plain text secrets."""
    plain_password = "super_secret_password_never_leak"
    settings_masked = Settings(
        POSTGRES_PASSWORD=SecretStr(plain_password),
        MIGRATION_POSTGRES_PASSWORD=SecretStr(plain_password),
        SECRET_KEY=SecretStr(plain_password),
    )

    settings_repr = repr(settings_masked)
    assert plain_password not in settings_repr
    assert "**********" in settings_repr

    dumped = settings_masked.model_dump()
    assert isinstance(dumped["POSTGRES_PASSWORD"], SecretStr)
    assert str(dumped["POSTGRES_PASSWORD"]) == "**********"


def test_invalid_configuration_handling() -> None:
    """Verify Pydantic validation rejects invalid types such as non-integer port."""
    with pytest.raises(ValidationError):
        Settings(POSTGRES_PORT="invalid_port_string")  # type: ignore[arg-type]
