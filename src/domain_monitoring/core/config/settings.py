from __future__ import annotations

from functools import cached_property, lru_cache
from pathlib import Path

from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .mailing import MailingSettings
from .postgres import PostgresSettings
from .redis import RedisSettings
from .log import LoggingSettings
from .urls import AppUrlSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_protocol: str
    app_host: str
    app_port: int = Field(gt=0, lt=65536)
    debug: bool

    postgres_host: str
    postgres_port: int = Field(gt=0, lt=65536)
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str

    redis_host: str
    redis_port: int = Field(gt=0, lt=65536)

    smtp_host: str
    smtp_port: int
    smtp_admin: str
    smtp_use_tls: bool = False
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )

    @cached_property
    def postgres(self) -> PostgresSettings:
        return PostgresSettings(
            host=self.postgres_host,
            port=self.postgres_port,
            user=self.postgres_user,
            password=self.postgres_password,
            db_name=self.postgres_db,
        )

    @cached_property
    def redis(self) -> RedisSettings:
        return RedisSettings(
            host=self.redis_host,
            port=self.redis_port,
        )

    @cached_property
    def mailing(self) -> MailingSettings:
        return MailingSettings(
            smtp_host=self.smtp_host,
            smtp_port=self.smtp_port,
            smtp_admin=self.smtp_admin,
            smtp_username=self.smtp_username,
            smtp_password=self.smtp_password,
            smtp_use_tls=self.smtp_use_tls,
        )

    @cached_property
    def logging(self) -> LoggingSettings:
        return LoggingSettings(
            level="DEBUG" if self.debug else "INFO",
        )

    @cached_property
    def urls(self):
        return AppUrlSettings(
            f"{self.app_protocol}://{self.app_host}:{self.app_port}",
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore
