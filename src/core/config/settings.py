from functools import cached_property, lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .mailing import MailingSettings
from .postgres import PostgresSettings
from .redis import RedisSettings
from .log import LoggingSettings

BASE_DIR = Path(__file__).resolve().parents[3]


class _Settings(BaseSettings):
    app_base_url: str
    debug: bool

    smtp_host: str
    smtp_port: int
    smtp_admin: str
    smtp_use_tls: bool = False
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str

    redis_host: str
    redis_port: int

    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        case_sensitive=False,
    )

    @cached_property
    def postgres(self) -> PostgresSettings:
        return PostgresSettings(
            host=self.postgres_host,
            port=self.postgres_port,
            user=self.postgres_user,
            password=self.postgres_password,
            db_name=self.postgres_db,
            echo=self.debug,
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


@lru_cache
def get_settings() -> _Settings:
    return _Settings()
